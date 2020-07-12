def update_resolver_lambda(temp_prefix, final_prefix, run_info, function_name, lambda_client):
    response = lambda_client.get_function(
        FunctionName=function_name
    )
    env = response['Configuration']['Environment']
    env['Variables']['run_info'] = run_info
    env['Variables']['temp_prefix'] = temp_prefix
    env['Variables']['final_prefix'] = final_prefix
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Environment=env
    )


def run_resolver_lambda(temp_prefix, final_prefix, run_info, function_name, lambda_client):
    update_resolver_lambda(temp_prefix, final_prefix, run_info, function_name, lambda_client)
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event'
    )