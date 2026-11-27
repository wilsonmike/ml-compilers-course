def withdraw(balance, amount):
    if amount > balance:
        raise ValueError(f"cannot take {amount} from {balance}")
    return balance - amount
