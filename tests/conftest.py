import os

# Los tests no llaman al juez LLM de objetivos (red): usan las palabras clave.
os.environ["JUEZ_MODELO"] = "off"
