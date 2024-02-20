import os
import logging
import datetime

import numpy as np
import pandas as pd
import tabulate
from dotenv import load_dotenv

from de_giro import DeGiroConnector
from processor import Config, minimize_distance_to_targets
from e_mail import send_outlook_email, messages

HISTORY_FOLDER = os.path.dirname(__file__) + "/history"

DF_OLD_FILENAME = "old_portfolio"
DF_NEW_FILENAME = "new_portfolio"

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def write_dataframes_to_history_folder(df_old: pd.DataFrame, df_new: pd.DataFrame) -> None:
    date = str(datetime.datetime.now().date())
    folder = f"{HISTORY_FOLDER}/{date}"

    try:
        os.mkdir(folder)
    except FileExistsError:
        logger.warning(f"Folder '{folder}' already exists. Using that.")

    df_old.to_excel(f"{HISTORY_FOLDER}/{date}/{DF_OLD_FILENAME}.xlsx", index=False)
    df_new.to_excel(f"{HISTORY_FOLDER}/{date}/{DF_NEW_FILENAME}.xlsx", index=False)


def main():
    logger.info("Loading environment variables")
    de_giro_username = os.getenv("DE_GIRO_USERNAME")
    de_giro_password = os.getenv("DE_GIRO_PASSWORD")
    from_email = os.getenv("FROM_EMAIL")
    outlook_password = os.getenv("EMAIL_PASSWORD")

    logger.info("Connecting to de Giro")
    connector = DeGiroConnector.login(de_giro_username, de_giro_password)

    logger.info("Loading portfolio")
    portfolio = connector.get_portfolio()
    df_portfolio = portfolio.to_dataframe()

    logger.info("Loading configuration")
    config = Config.from_json_file(r"inputs.json")

    # TODO: implement searching of products not in portfolio and getting their id_nr

    df_portfolio['target_share'] = df_portfolio['symbol'].map(config.target_shares)

    logger.info("Analyzing what to do...")
    minimize_result = minimize_distance_to_targets(
        ids=np.array(df_portfolio["id_nr"]),
        targets=np.array(df_portfolio["target_share"]),
        values=np.array(df_portfolio["value"]),
        steps=np.array(df_portfolio["price"]),
        additional_space=portfolio.unused_amount,
    )

    logger.info("Done, merging results")
    df_new_portfolio = df_portfolio.merge(
        pd.DataFrame(list(zip(minimize_result.ids, minimize_result.new_shares, minimize_result.steps)),
                     columns=["id_nr", "new_shares", "orders"]),
        on=["id_nr"]
    )

    df_new_portfolio["new_quantity"] = df_new_portfolio["quantity"] + df_new_portfolio["orders"]
    df_new_portfolio["new_value"] = df_new_portfolio["new_quantity"] * df_new_portfolio["price"]

    logger.info("Performing actions")
    actions = minimize_result.get_actions()
    if len(actions) == 0:
        logger.info("Nothing to do.")
        message = messages.NOTHING_TO_DO.format(
            remaining_amount=round(minimize_result.remaining_amount, 2),
        )
    else:
        for action in actions:
            #connector.buy_order(product_id=action.id_nr, amount=action.amount, limit=action.limit)
            action.print()

        message = messages.PORTFOLIO_UPDATE.format(
            available_amount=portfolio.unused_amount,
            remaining_amount=round(minimize_result.remaining_amount, 2),
            buy_orders=minimize_result.to_string(
                human_readables={product.id_nr: product.name for product in portfolio.items}
            ),
            position_overview=tabulate.tabulate(
                df_new_portfolio[["symbol", "new_quantity", "new_value", "new_shares"]].round(2),
                headers=["Name", "Quantity", "Value", "Share"],
                showindex=False,
            )
        )

    logger.info("Writing data to history folder")
    write_dataframes_to_history_folder(df_portfolio, df_new_portfolio)

    logger.info("Sending email")
    send_outlook_email(from_email, config.to_email, outlook_password, message, subject="Portfolio update")

    logger.info("Logging out")
    connector.logout()


if __name__ == '__main__':
    main()
