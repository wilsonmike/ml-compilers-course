type suit = Hearts | Diamonds | Clubs | Spades
type card =
  | Number of int * suit        (* 2 through 10 *)
  | Jack of suit | Queen of suit | King of suit
  | Ace of suit

let hand_value (hand : card list) : int =
  let points = function Number (n, _) -> n | Jack _ | Queen _ | King _ -> 10 | Ace _ -> 11 in
  let total = List.fold_left (fun acc c -> acc + points c) 0 hand in
  let aces = List.length (List.filter (function Ace _ -> true | _ -> false) hand) in
  let rec soften t a = if t > 21 && a > 0 then soften (t - 10) (a - 1) else t in
  soften total aces
