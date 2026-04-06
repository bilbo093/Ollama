# 使用指南

## 命令格式

```bash
python main.py <模式> -i <输入文件> -o <输出文件>
```

## 模式对比

| 模式 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `full` | 生成总结与展望 | .txt/.docx | .txt |
| `chapter` | 生成各章总结 | .txt/.docx | .txt |
| `paragraph` | 语法检查润色 | .txt/.docx | .txt + .docx |

## 全文模式

```bash
python main.py full -i input.txt -o output.txt
python main.py full -i input.docx -o output.txt
```

## 章节模式

```bash
python main.py chapter -i input.txt -o output.txt
```

## 段落模式

```bash
# 自动推断输出文件
python main.py paragraph -i input.docx

# 指定检查结果文件
python main.py paragraph -i input.docx -o check.txt
```

**输出**:
- `<文件名>_grammar.txt` - 检查结果
- `<文件名>_fixed.docx` - 润色后文档（与输入文件同目录）
