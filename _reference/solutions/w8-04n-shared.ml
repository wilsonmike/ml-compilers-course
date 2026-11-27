let shared_lines (ty : string) (name : string) (n : int) : string list =
  [Printf.sprintf "__shared__ %s %s[%d];" ty name n;
   Printf.sprintf "for (int32_t z_ = threadIdx.x; z_ < %d; z_ += blockDim.x) %s[z_] = 0;" n name;
   "__syncthreads();"]
