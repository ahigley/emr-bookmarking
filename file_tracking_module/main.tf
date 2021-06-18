variable "job_tracked_prefixes" {
  type = map(object({
    bucket        = string
    prefix        = string
    job_name      = string
    max_count     = number
    reset_cpu     = number
    reset_memory  = number
    rewind_cpu    = number
    rewind_memory = number
  }))
}