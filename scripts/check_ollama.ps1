$ErrorActionPreference = "Stop"

$model = $env:OLLAMA_MODEL
if (-not $model) {
    $model = "qwen3:4b"
}

Write-Host "Checking Ollama model: $model"
ollama list
ollama run $model "Answer with only: ready"

