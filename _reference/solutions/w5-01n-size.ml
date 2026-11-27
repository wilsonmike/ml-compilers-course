let size (shape : int list) : int =
  List.fold_left ( * ) 1 shape
