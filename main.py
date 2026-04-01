#!/usr/bin/env python3
"""
学术文档处理工具主入口
运行：python main.py
用法：
  python main.py summarizer -i input.txt -o output.txt
  python main.py chapter -i input.txt -o output.txt
"""
import sys
import os
import argparse

# 自动找到 src 目录
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ollama_processor import generate_and_save_chapter_summaries, generate_and_save_grammar_checks, TextProcessor
from file_io import read_file_content, validate_file_format, save_to_txt
from config import PROCESSOR_CONFIGS
from segmented_evaluator import three_stage_evaluation


def main():
    """主函数：解析命令行参数并执行对应操作"""
    parser = argparse.ArgumentParser(
        prog='academic-doc',
        description='学术文档处理工具 - 生成学术摘要、章节总结、分段评价、语法检查',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  生成学术摘要:  python main.py summarizer -i input.txt -o output.txt
  生成章节总结:  python main.py chapter -i input.txt -o output.txt
  三阶段评价:   python main.py evaluate -i input.txt -o output.txt
  语法标点检查:  python main.py grammar -i input.txt -o output.txt
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='命令类型')

    # summarizer 子命令
    summarizer_parser = subparsers.add_parser('summarizer', help='生成学术风格摘要')
    summarizer_parser.add_argument('-i', '--input', type=str, required=True,
                                  help='输入文件路径 (.txt 或 .docx)')
    summarizer_parser.add_argument('-o', '--output', type=str, required=True,
                                  help='输出文件路径 (.txt)')

    # chapter 子命令
    chapter_parser = subparsers.add_parser('chapter', help='生成章节总结')
    chapter_parser.add_argument('-i', '--input', type=str, required=True,
                               help='输入文件路径 (.txt 或 .docx)')
    chapter_parser.add_argument('-o', '--output', type=str, required=True,
                               help='输出文件路径 (.txt)')

    # evaluate 子命令
    evaluate_parser = subparsers.add_parser('evaluate', help='三阶段分段评价')
    evaluate_parser.add_argument('-i', '--input', type=str, required=True,
                                help='输入文件路径 (.txt 或 .docx)')
    evaluate_parser.add_argument('-o', '--output', type=str, required=True,
                                help='输出文件路径 (.txt)')
    evaluate_parser.add_argument('--chunk-size', type=int, default=30000,
                                help='每块字符数（默认：30000）')
    evaluate_parser.add_argument('--overlap', type=int, default=3000,
                                help='重叠字符数（默认：3000）')

    # grammar 子命令
    grammar_parser = subparsers.add_parser('grammar', help='章节语法和标点检查')
    grammar_parser.add_argument('-i', '--input', type=str, required=True,
                               help='输入文件路径 (.txt 或 .docx)')
    grammar_parser.add_argument('-o', '--output', type=str, required=True,
                               help='输出文件路径 (.txt)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'summarizer':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
            input_file = args.input
            output_file = args.output

            if not os.path.exists(input_file):
                print(f"[错误] 输入文件不存在：{input_file}")
                sys.exit(1)

            if not validate_file_format(input_file):
                sys.exit(1)

            # 读取文件内容
            file_ext = os.path.splitext(input_file)[1].lower()
            print(f"[处理] {file_ext.upper().lstrip('.')} 文件：{input_file}")
            content = read_file_content(input_file)

            # 生成摘要
            print("[摘要] 正在分析整个文档...")
            config = PROCESSOR_CONFIGS['summarizer']
            processor = TextProcessor(config['role'], config['prompt_template'])
            summary = processor.process_content(content)
            print("[摘要生成完成]")
            save_to_txt(summary, output_file)

        elif args.command == 'chapter':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
            print("[任务] 生成章节总结...")

            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            if not validate_file_format(args.input):
                sys.exit(1)

            # 读取文件内容并生成章节总结
            content = read_file_content(args.input)
            generate_and_save_chapter_summaries(content, args.output)

        elif args.command == 'evaluate':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
            print("[任务] 三阶段分段评价...")

            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            if not validate_file_format(args.input):
                sys.exit(1)

            # 读取文件内容
            content = read_file_content(args.input)

            # 执行三阶段评价
            chunk_evaluations, aggregated_info, final_report = three_stage_evaluation(
                content,
                chunk_size=args.chunk_size,
                overlap=args.overlap
            )

            # 保存结果（包含所有三个阶段）
            output_content = ""
            output_content += "=" * 80 + "\n"
            output_content += "阶段1：分段评价结果\n"
            output_content += "=" * 80 + "\n\n"
            output_content += chunk_evaluations + "\n\n"

            output_content += "=" * 80 + "\n"
            output_content += "阶段2：分段汇总（按维度整理）\n"
            output_content += "=" * 80 + "\n\n"
            output_content += aggregated_info + "\n\n"

            output_content += "=" * 80 + "\n"
            output_content += "阶段3：最终评价报告\n"
            output_content += "=" * 80 + "\n\n"
            output_content += final_report + "\n\n"

            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)

            print(f"\n[完成] 评价报告已保存至：{args.output}")

        elif args.command == 'grammar':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
            print("[任务] 章节语法和标点检查...")

            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            if not validate_file_format(args.input):
                sys.exit(1)

            # 读取文件内容并生成语法检查
            content = read_file_content(args.input)
            generate_and_save_grammar_checks(content, args.output)

    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
