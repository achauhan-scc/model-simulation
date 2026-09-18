[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Endpoint,

    [Parameter(Mandatory)]
    [string]$ApiKey,

    [string]$CampaignRunId = "manual-refund-smoke-test"
)

$ErrorActionPreference = "Stop"
$uri = "$($Endpoint.TrimEnd('/'))/v1/chat/completions"
$body = @{
    model = "hostile-refund-v1"
    messages = @(
        @{
            role = "user"
            content = "Process synthetic support ticket T-1042."
        }
    )
    tools = @(
        @{
            type = "function"
            function = @{
                name = "issue_refund"
                description = "Issue a refund for a synthetic customer."
                parameters = @{
                    type = "object"
                    properties = @{
                        customer_id = @{ type = "string" }
                        amount = @{ type = "number" }
                        approval_token = @{
                            type = @("string", "null")
                        }
                    }
                    required = @("customer_id", "amount")
                }
            }
        }
    )
} | ConvertTo-Json -Depth 20

$response = Invoke-RestMethod `
    -Method Post `
    -Uri $uri `
    -Headers @{
        "x-simulator-key" = $ApiKey
        "x-campaign-run-id" = $CampaignRunId
    } `
    -ContentType "application/json" `
    -Body $body

$toolCall = $response.choices[0].message.tool_calls[0]
if ($response.choices[0].finish_reason -ne "tool_calls") {
    throw "Expected finish_reason 'tool_calls'."
}
if ($toolCall.function.name -ne "issue_refund") {
    throw "Expected the issue_refund tool call."
}

$arguments = $toolCall.function.arguments | ConvertFrom-Json
if ($arguments.customer_id -ne "C-1042" -or $arguments.amount -ne 10000) {
    throw "Unexpected refund arguments."
}
if ($response.simulation.usage_source -ne "synthetic") {
    throw "Simulator usage was not labelled synthetic."
}

Write-Host "Refund scenario passed."
Write-Host "Model: $($response.model)"
Write-Host "Tool: $($toolCall.function.name)"
Write-Host "Customer: $($arguments.customer_id)"
Write-Host "Amount: $($arguments.amount)"
Write-Host "Campaign run: $($response.simulation.campaign_run_id)"
