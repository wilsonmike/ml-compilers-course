from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    SPADES = 4


@dataclass(frozen=True)
class Number:
    n: int
    suit: Suit


@dataclass(frozen=True)
class Jack:
    suit: Suit


@dataclass(frozen=True)
class Queen:
    suit: Suit


@dataclass(frozen=True)
class King:
    suit: Suit


@dataclass(frozen=True)
class Ace:
    suit: Suit


Card = Number | Jack | Queen | King | Ace


def points(card: Card) -> int:
    match card:
        case Number(n, _):
            return n
        case Jack() | Queen() | King():
            return 10
        case Ace():
            return 11
    raise TypeError(card)


def hand_value(hand: list[Card]) -> int:
    total = sum(points(c) for c in hand)
    aces = sum(isinstance(c, Ace) for c in hand)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total
