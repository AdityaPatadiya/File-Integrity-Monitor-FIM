import getpass


class Authentication:

    def authorised_credentials(self):
        entered_password = getpass.getpass("Enter the password:")
        if entered_password == "123":
            print("Authentication Successful.")
        else:
            print("Access denied! Incorrect password.")
            exit(1)
