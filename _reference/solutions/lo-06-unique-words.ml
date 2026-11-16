module StringSet = Set.Make (String)

let unique_words (words : string list) : string list =
  StringSet.elements (StringSet.of_list words)
