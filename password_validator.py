import string

from pathlib import Path


class Singleton(type):
    """Metaclass that makes class a singleton."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class PasswordException(Exception):
    pass


class PasswordValidatorException(Exception):
    pass


class PasswordValidator(metaclass=Singleton):
    def __init__(self, min_length: int = 10, max_length=48, password_lists: Path = None):

        self.password_cap = None
        self.password_low = None
        self.password_length = None
        self.known_passwords = set()

        if max_length < min_length:
            raise PasswordValidatorException(
                f"min_length ({min_length}) must be shorter than max_length ({max_length})"
            )

        self.min_length = min_length
        self.max_length = max_length
        self.password_lists = password_lists

        self.__load_password_list()

    def validate(self, password: str) -> bool:
        self.password_length = len(password)

        self.__check_length(password)
        self.__check_digits(password)
        self.__check_whitespace(password)
        self.__check_known_password(password)
        return True

    def get_known_passwords_amount(self) -> int:
        return len(self.known_passwords)

    def __load_password_list(self) -> None:

        self.__add_trivial_known_passwords()

        if self.password_lists is None:
            return

        if not self.password_lists.is_dir():
            return

        for list_path in self.password_lists.iterdir():
            if str(list_path).endswith('.txt') and list_path.is_file():
                with open(list_path, "r") as pass_file:
                    for kp in pass_file:
                        kp = kp.strip()
                        kp2 = kp + kp
                        self.__add_known_password(kp)
                        self.__add_known_password(kp2)

    def __add_trivial_known_passwords(self):
        for alphabet in [string.ascii_lowercase, string.ascii_lowercase[::-1]]:
            [
                self.__add_known_password(alphabet[i:j])
                for i in range(len(alphabet))
                for j in range(i + 1, len(alphabet) + 1)
            ]

    def __add_known_password(self, kp: str):
        if self.min_length <= len(kp) <= self.max_length and not self.__has_whitespace(kp):
            self.known_passwords.add(kp)

    def __check_length(self, password: str):
        if len(password) < self.min_length:
            raise PasswordException(f"Password must be at least {self.min_length} characters long!")

        if len(password) > self.max_length:
            raise PasswordException(f"Passwords with more than {self.max_length} characters are not allowed!")

    def __check_digits(self, password: str):

        if password.isdigit():
            raise PasswordException(f"Passwords containing only digits are not allowed!")

        if self.__has_to_much_digits(password):
            raise PasswordException(f"Short passwords with more than 50% digits are not allowed!")

    def __check_whitespace(self, password: str):
        if self.__has_whitespace(password):
            raise PasswordException(f"Non printable characters are not allowed in passwords (e.g. whitespace)!")

    def __check_known_password(self, password: str):
        if password in self.known_passwords:
            raise PasswordException(f"Password in known password list")

    @staticmethod
    def __has_whitespace(password: str) -> bool:
        for char in password:
            if not char.isprintable() or char.isspace():
                return True
        return False

    def __has_to_much_digits(self, password: str) -> bool:

        if len(password) > self.min_length * 2:
            return False

        digits = 0
        for char in password:
            if char.isdigit():
                digits += 1

        if digits > len(password) // 2:
            return True

        return False


if __name__ == "__main__":
    try:
        pv = PasswordValidator(password_lists=Path("./wordlists"))
        password = "passwd123456"
        pv.validate(password)
        print(f"known passwords: {pv.get_known_passwords_amount()}")
        print(password)
    except PasswordException as e:
        print(e)
