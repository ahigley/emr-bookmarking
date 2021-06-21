resource "null_resource" "deploy_reset_to_ecr" {
  for_each = var.job_tracked_prefixes
  # Run on initial creation and any time the prefix is changed
  triggers = {
    ecs_reset_task = aws_ecs_task_definition.first_run_or_reset[each.key].id
    prefix = each.value.prefix
  }

  provisioner "local-exec" {
    #TODO left off here
    command = "TODO"
  }
  depends_on = [aws_ecs_task_definition.first_run_or_reset[each.key]]
}