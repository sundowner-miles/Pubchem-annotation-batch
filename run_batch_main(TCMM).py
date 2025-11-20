import os, sys, argparse

# 将项目根加入 sys.path，方便导入同目录上层的模块（根据你的工程结构调整）
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # 两级上层到 pubchem-annotation-batch 根
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

parser = argparse.ArgumentParser(description="Run batch annotation (resume-capable).")
parser.add_argument("--file_path", "-f", default="data/inputs/Herb-Ingredient_csmiles_replaced_processed(TCMM).csv", help="输入表路径")
parser.add_argument("--cid", default=None, help="CID 列名")
parser.add_argument("--smiles", default="cleaned_smiles", help="SMILES 列名")
parser.add_argument("--out", default="output/smiles_annotation关联结果(TCMM).csv", help="输出文件路径（可选）")
parser.add_argument("--delay", type=float, default=0.05)
parser.add_argument("--save-every", type=int, default=20)
parser.add_argument("--max-rows", type=int, default=None)
parser.add_argument("--sample", action="store_true")
parser.add_argument("--batch-start", type=int, default=None)
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

# 尝试导入批处理函数（假设你已将 notebook 转为 get_annotation.py 或把函数放到模块）
try:
    # 优先从可能的模块名导入
    from src.pubchem import process_annotations
except Exception:
    try:
        from src.pubchem import process_annotations  # 再次尝试（占位）
    except Exception as e:
        print("无法从 get_annotation 模块导入 process_annotations_resume。")
        print("请将 notebook 中的 process_annotations_resume 和依赖函数导出为 get_annotation.py，"
              "或把相关函数放到可导入的模块中。")
        print("错误详情:", e)
        sys.exit(2)

# 调用批处理（支持断点续跑）
process_annotations(
    file_path=args.file_path,
    cid_name=args.cid,
    smiles_name=args.smiles,
    out_path=args.out,
    delay=args.delay,
    save_every=args.save_every,
    max_rows=args.max_rows,
    sample=args.sample,
    batch_start=args.batch_start,
    verbose=args.verbose
)