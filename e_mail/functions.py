import smtplib
import ssl
import email


context = ssl.create_default_context()


def send_outlook_email(
        from_email: str,
        to_email: str,
        password: str,
        text: str,
        subject: str,
) -> None:
    message = email.message.EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email

    message.set_content(text)

    with smtplib.SMTP("smtp.office365.com") as server:
        server.starttls(context=context)
        server.login(from_email, password)
        server.sendmail(from_addr=from_email, to_addrs=to_email, msg=message.as_string())
