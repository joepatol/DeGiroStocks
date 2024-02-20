# What is this?

This repository contains a wrapper around the non-public DeGiro API. Hence, it cannot be guaranteed to work. 

It can be used to login and load your portfolio. It can also be used to buy shares with a basic strategy

# How to use the main script

You can run the main script to download your portfolio and buy new shares to get your portfolio as close as possible to a target division.

E.g. you want a 0.5/0.5 ratio in your portfolio of stockA/stockB

When the script finished it will send an email to a specified email address.

create a `.env` file like below

```
DE_GIRO_USERNAME=<yourusername>
DE_GIRO_PASSWORD=<yourpassword>
FROM_EMAIL=<some_email_address>
EMAIL_PASSWORD=<password_email_account>
```

Then configure `inputs.json`

```json
{
  "target_shares": {
    "VUSA": 0.6,
    "VWRL": 0.3,
    "VFEM": 0.05,
    "IQQH": 0.05
  },
  "to_email": "",
  "strategy": ""
}
```