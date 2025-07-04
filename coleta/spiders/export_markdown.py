# %%
import nbformat
from pathlib import Path

# Caminho do seu notebook
notebook_path = Path("plot_aluguel_fpolis.ipynb")
output_path = Path("markdown_extraido.md")

# Lê o notebook
with notebook_path.open("r", encoding="utf-8") as f:
    notebook = nbformat.read(f, as_version=4)

# Escreve o conteúdo no arquivo Markdown
with output_path.open("w", encoding="utf-8") as out:
    for cell in notebook.cells:
        # Exporta células Markdown
        if cell.cell_type == "markdown":
            out.write(cell.source.strip() + "\n\n---\n\n")

        # Exporta células de código com seus outputs
        elif cell.cell_type == "code":
            out.write("```python\n" + cell.source.strip() + "\n```\n")

            # Exporta outputs (somente texto)
            for output in cell.get("outputs", []):
                if output.output_type == "stream":  # print, stdout
                    out.write("```\n" + output.text.strip() + "\n```\n")
                elif output.output_type == "execute_result":
                    data = output.get("data", {}).get("text/plain", "")
                    if data:
                        out.write("```\n" + data.strip() + "\n```\n")
            
            out.write("\n---\n\n")

print(f"Exportado com sucesso para: {output_path.resolve()}")
