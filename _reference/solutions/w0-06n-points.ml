type suit = Hearts | Diamonds | Clubs | Spades
type card =
  | Number of int * suit
  | Jack of suit | Queen of suit | King of suit
  | Ace of suit
  | Joker

let points (c : card) : int =
  match c with
  | Number (n, _) -> n
  | Jack _ | Queen _ | King _ -> 10
  | Ace _ -> 11
  | Joker -> 0
