import os
from dotenv import load_dotenv
load_dotenv()

RocketInStToken = os.getenv("RocketInStToken")

def main():
    print("RocketInStToken:", RocketInStToken)


if __name__ == "__main__":
    main()
