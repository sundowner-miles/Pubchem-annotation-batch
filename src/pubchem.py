import time, random, requests
import pandas as pd
import os, sys
import re
import time as _time
import random as _random
from tqdm import tqdm

def fetch_annotation_by_cid(cid, retries=3, backoff=1.5, verbose=False):
    """
    Fetch annotation from PubChem API using the provided CID.
    Implements retry logic in case of failures.
    Returns the name and description of the compound.
    """

    if cid is None:
        return None, None
    cid_str = str(cid).strip()
    if not cid_str or cid_str.lower() in {"nan", "none"}:
        return None, None

    headers = {"User-Agent": "python-requests/1.0 (contact: none)", "Cache-Control": "no-cache"}

    # 1) synonyms 作为候选 name
    name = None
    syn_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid_str}/synonyms/JSON"
    try:
        if verbose:
            print("Prepared synonyms URL:", syn_url)
        r = requests.get(syn_url, timeout=10, headers=headers)
        if verbose:
            print("Synonyms ->", r.url, r.status_code)
        if r.status_code == 200:
            j = r.json()
            info = j.get("InformationList", {}).get("Information", [])
            if info:
                syns = info[0].get("Synonym", [])
                if syns:
                    name = syns[0]
    except Exception as e:
        if verbose:
            print("synonyms 请求异常:", e)

    # 2) compound-specific 页面（优先）
    compound_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid_str}/JSON"
    if verbose:
        print("Compound data URL:", compound_url)

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(compound_url, timeout=12, headers=headers)
            if verbose:
                print(f"GET {r.url} -> {r.status_code}")
            if r.status_code != 200:
                if attempt == retries and verbose:
                    print(f"CID {cid_str} compound page 非200: {r.status_code}")
                time.sleep(min(backoff ** attempt + random.random(), 5))
                continue

            data = r.json()
            record = data.get("Record", {}) or {}

            # 递归查找包含目标 heading 的 sections
            def find_sections(sections, target="Record Description"):
                res = []
                for s in sections or []:
                    # 多种字段名兼容
                    heading = None
                    toc = s.get("TOCHeading")
                    if isinstance(toc, dict):
                        heading = toc.get("#TOCHeading") or toc.get("TOCHeading")
                    if not heading:
                        heading = s.get("TOCHeading") or s.get("Heading")
                    if heading and target.lower() in str(heading).lower():
                        res.append(s)
                    # 递归子 section（可能字段名不同）
                    subs = s.get("Section") or s.get("Sections") or s.get("SectionList") or []
                    if subs:
                        res.extend(find_sections(subs, target=target))
                return res

            sections = record.get("Section") or record.get("Sections") or []
            rd_secs = find_sections(sections, target="Record Description")
            if verbose:
                print("Record Description sections found:", len(rd_secs))

            # 文本提取器（递归，支持 StringWithMarkup / String / 嵌套结构）
            def extract_texts_from_data(data_block):
                texts = []
                def _ext(o):
                    if isinstance(o, dict):
                        if "StringWithMarkup" in o:
                            for itm in o["StringWithMarkup"] if isinstance(o["StringWithMarkup"], list) else []:
                                if isinstance(itm, dict) and "String" in itm and isinstance(itm["String"], str):
                                    texts.append(itm["String"])
                        elif "String" in o and isinstance(o["String"], str):
                            texts.append(o["String"])
                        else:
                            for v in o.values():
                                _ext(v)
                    elif isinstance(o, list):
                        for it in o:
                            _ext(it)
                _ext(data_block)
                return [t for t in texts if t and isinstance(t, str)]

            # 在 Record Description sections 中提取第一个合理的 description
            for sec in rd_secs:
                # 常见位置：Information / InformationList / Data
                infos = sec.get("Information") or sec.get("InformationList") or sec.get("Data") or []
                if isinstance(infos, dict):
                    infos = [infos]
                for info in infos or []:
                    # 信息块中可能有 Value / ValueList / Data
                    val = info.get("Value") or info.get("ValueList") or info.get("Data") or info.get("ValueString")
                    texts = extract_texts_from_data(val)
                    if texts:
                        desc = "\n".join(texts[:6])
                        if verbose:
                            print("Found Record Description (truncated):", desc[:200])
                        return (name or sec.get("TOCHeading") or sec.get("Heading")), desc

                # 有时 section 自身也直接包含 Data 字段
                data_items = sec.get("Data") or sec.get("Information") or []
                texts = extract_texts_from_data(data_items)
                if texts:
                    desc = "\n".join(texts[:6])
                    if verbose:
                        print("Found description in section fallback (truncated):", desc[:200])
                    return (name or sec.get("TOCHeading") or sec.get("Heading")), desc

            # 未找到 Record Description -> 返回 name（若有）并退出
            if verbose:
                print("No Record Description found in compound page for CID", cid_str)
            return name, None

        except Exception as e:
            if attempt == retries and verbose:
                print(f"请求错误 {cid_str}: {e}")
            time.sleep(min(backoff ** attempt + random.random(), 5))

    return name, None

def fetch_annotation_by_smiles(smiles, retries=3, backoff=1.5, verbose=False):
    """
    从 PubChem compound page 获取注释（优先 Record Description）。
    输入：SMILES 字符串
    返回：(name_or_None, description_or_None)
    """

    # ==================== 新增：SMILES 预处理与校验 ====================
    if smiles is None:
        return None, None
    smiles_str = str(smiles).strip()
    # 过滤无效 SMILES（空值、纯空格、nan/None）
    if not smiles_str or smiles_str.lower() in {"nan", "none"}:
        if verbose:
            print("无效 SMILES：空值或非法字符串")
        return None, None
    # 简单清洗：去除 SMILES 中的非法字符（如引号、换行符）
    smiles_str = re.sub(r'["\n\r\t]', '', smiles_str)
    if verbose:
        print(f"处理 SMILES：{smiles_str}")

    headers = {"User-Agent": "python-requests/1.0 (contact: none)", "Cache-Control": "no-cache"}

    # ==================== 新增：SMILES → CID 转换 ====================
    cid = None
    smiles_to_cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles_str}/cids/TXT"
    try:
        if verbose:
            print("SMILES 转 CID 请求 URL:", smiles_to_cid_url)
        # PubChem SMILES 转 CID 接口需用 POST 方法，数据为 SMILES 字符串
        r = requests.post(
            smiles_to_cid_url,
            data=smiles_str,
            headers=headers,
            timeout=10
        )
        if verbose:
            print(f"SMILES → CID 响应状态码: {r.status_code}")
        if r.status_code == 200:
            cid_str = r.text.strip()
            if cid_str.isdigit():
                cid = int(cid_str)
                if verbose:
                    print(f"成功获取 CID：{cid}")
            else:
                if verbose:
                    print(f"SMILES 转 CID 失败：返回非数字结果 '{cid_str}'")
        else:
            if verbose:
                print(f"SMILES 转 CID 失败：状态码 {r.status_code}，响应内容：{r.text[:100]}")
    except Exception as e:
        if verbose:
            print(f"SMILES 转 CID 请求异常: {e}")
    # 若 CID 获取失败，直接返回空结果
    if cid is None:
        return None, None, None


    # ==================== 复用原逻辑：CID → 名称 + 注释 ====================
    # 1) 从 CID 获取同义词（作为候选 name）
    name = None
    syn_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
    try:
        if verbose:
            print("Prepared synonyms URL:", syn_url)
        r = requests.get(syn_url, timeout=10, headers=headers)
        if verbose:
            print("Synonyms ->", r.url, r.status_code)
        if r.status_code == 200:
            j = r.json()
            info = j.get("InformationList", {}).get("Information", [])
            if info:
                syns = info[0].get("Synonym", [])
                if syns:
                    name = syns[0]
    except Exception as e:
        if verbose:
            print("synonyms 请求异常:", e)

    # 2) 从 CID 获取 compound-specific 页面，提取 Record Description
    compound_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
    if verbose:
        print("Compound data URL:", compound_url)

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(compound_url, timeout=12, headers=headers)
            if verbose:
                print(f"GET {r.url} -> {r.status_code}")
            if r.status_code != 200:
                if attempt == retries and verbose:
                    print(f"CID {cid} compound page 非200: {r.status_code}")
                time.sleep(min(backoff ** attempt + random.random(), 5))
                continue

            data = r.json()
            record = data.get("Record", {}) or {}

            # 递归查找包含目标 heading 的 sections
            def find_sections(sections, target="Record Description"):
                res = []
                for s in sections or []:
                    # 多种字段名兼容
                    heading = None
                    toc = s.get("TOCHeading")
                    if isinstance(toc, dict):
                        heading = toc.get("#TOCHeading") or toc.get("TOCHeading")
                    if not heading:
                        heading = s.get("TOCHeading") or s.get("Heading")
                    if heading and target.lower() in str(heading).lower():
                        res.append(s)
                    # 递归子 section（可能字段名不同）
                    subs = s.get("Section") or s.get("Sections") or s.get("SectionList") or []
                    if subs:
                        res.extend(find_sections(subs, target=target))
                return res

            sections = record.get("Section") or record.get("Sections") or []
            rd_secs = find_sections(sections, target="Record Description")
            if verbose:
                print("Record Description sections found:", len(rd_secs))

            # 文本提取器（递归，支持 StringWithMarkup / String / 嵌套结构）
            def extract_texts_from_data(data_block):
                texts = []
                def _ext(o):
                    if isinstance(o, dict):
                        if "StringWithMarkup" in o:
                            for itm in o["StringWithMarkup"] if isinstance(o["StringWithMarkup"], list) else []:
                                if isinstance(itm, dict) and "String" in itm and isinstance(itm["String"], str):
                                    texts.append(itm["String"])
                        elif "String" in o and isinstance(o["String"], str):
                            texts.append(o["String"])
                        else:
                            for v in o.values():
                                _ext(v)
                    elif isinstance(o, list):
                        for it in o:
                            _ext(it)
                _ext(data_block)
                return [t for t in texts if t and isinstance(t, str)]

            # 在 Record Description sections 中提取第一个合理的 description
            for sec in rd_secs:
                # 常见位置：Information / InformationList / Data
                infos = sec.get("Information") or sec.get("InformationList") or sec.get("Data") or []
                if isinstance(infos, dict):
                    infos = [infos]
                for info in infos or []:
                    # 信息块中可能有 Value / ValueList / Data
                    val = info.get("Value") or info.get("ValueList") or info.get("Data") or info.get("ValueString")
                    texts = extract_texts_from_data(val)
                    if texts:
                        desc = "\n".join(texts[:6])
                        if verbose:
                            print("Found Record Description (truncated):", desc[:200])
                        return cid, (name or sec.get("TOCHeading") or sec.get("Heading")), desc

                # 有时 section 自身也直接包含 Data 字段
                data_items = sec.get("Data") or sec.get("Information") or []
                texts = extract_texts_from_data(data_items)
                if texts:
                    desc = "\n".join(texts[:6])
                    if verbose:
                        print("Found description in section fallback (truncated):", desc[:200])
                    return cid, (name or sec.get("TOCHeading") or sec.get("Heading")), desc

            # 未找到 Record Description -> 返回 name（若有）并退出
            if verbose:
                print("No Record Description found in compound page for CID", cid)
            return cid, name, None

        except Exception as e:
            if attempt == retries and verbose:
                print(f"请求错误 {cid}: {e}")
            time.sleep(min(backoff ** attempt + random.random(), 5))

    return cid, name, None

def process_annotations(file_path,
                        cid_name=None,
                        smiles_name=None,
                        out_path=None,
                        delay=0.2,
                        save_every=20,
                        max_rows=None,
                        sample=False,
                        batch_start=None,
                        verbose=False):
    """
    Batch process annotations with resume support.

    Parameters:
      file_path: 输入表格路径
      cid_name: 期望的 CID 列名（会做模糊匹配）
      smiles_name: 期望的 SMILES 列名（会做模糊匹配）
      out_path: 输出 CSV 路径（默认输入目录下 smiles_annotation关联结果.csv）
      delay: 每次请求后的延时（秒）
      save_every: 每多少条写一次磁盘
      max_rows: 最多处理多少条（None 为全部）
      sample: 若为 True 且 max_rows 不为 None，则随机抽样 max_rows 条
      batch_start: 手动指定从哪个索引开始（用于跳过前若干行）
      verbose: 输出调试信息
    """

    # 读取表格，兼容常见编码与分隔符
    df = None
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin1"):
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        raise RuntimeError(f"无法读取文件 {file_path}，请检查编码/格式。")

    # 规范化列名
    df.columns = [re.sub(r'\s+', ' ', str(c)).strip().replace('\u00A0', ' ') for c in df.columns]
    if verbose:
        print("Detected columns:", df.columns.tolist())

    def find_col(target, keywords=None):
        if target in df.columns:
            return target
        low = target.lower()
        for c in df.columns:
            if low == str(c).lower():
                return c
        kws = keywords or [part for part in re.split(r'[\s_\-]+', target.lower()) if part]
        for c in df.columns:
            lc = str(c).lower()
            if all(k in lc for k in kws):
                return c
        return None

    cid_col = find_col(cid_name, keywords=['cid', 'pubchem']) if cid_name is not None else None
    smiles_col = find_col(smiles_name, keywords=['smiles', 'csmiles', 'smile']) if smiles_name is not None else None
    if cid_col is None and smiles_col is None:
        raise KeyError(f"找不到列。期望: '{cid_name}' 和 '{smiles_name}'。可用列: {df.columns.tolist()}")

    if cid_col is not None:
        cid_list = df[cid_col].astype(str).tolist()
    if smiles_col is not None:
        smiles_list = df[smiles_col].astype(str).tolist()

    total = len(smiles_list)
    indices = list(range(total))

    # 按 max_rows / sample 筛选索引
    if isinstance(max_rows, int) and max_rows > 0:
        if sample:
            indices = _random.sample(indices, min(max_rows, total))
        else:
            indices = indices[:min(max_rows, total)]

    start_idx = batch_start if batch_start is not None else 0
    if start_idx < 0:
        start_idx = 0

    # 读取已处理 smiles，跳过已完成部分（根据输出文件中的 smiles 列）
    processed = set()
    header_needed = True
    if os.path.exists(out_path):
        try:
            prev = pd.read_csv(out_path, encoding='utf-8-sig')
            for _, r in prev.iterrows():
                processed.add(str(r.get('smiles')))
            header_needed = False
            if verbose:
                print(f"已加载 {len(prev)} 现有结果，将跳过这些 CIDs。")
        except Exception:
            if verbose:
                print("无法读取已存在的输出文件，重新从头开始写入。")
            processed = set()
            header_needed = True

    def _append_df_to_csv(path, df_to_append, header, verbose=False):
        """
        Append df to CSV atomically. 返回 (ok, err).
        会在同目录写临时文件再原子替换，减少中途写入丢失的可能性。
        """
        import tempfile, shutil
        try:
            out_dir = os.path.dirname(os.path.abspath(path))
            os.makedirs(out_dir, exist_ok=True)
            # 如果目标不存在且 header=True，则直接写（create）
            if not os.path.exists(path) and header:
                if verbose:
                    print("Creating new CSV:", path)
                df_to_append.to_csv(path, index=False, encoding='utf-8-sig', header=True)
                return True, None
            # 否则把追加内容写到临时文件，然后合并/追加到目标
            # 临时文件写入后再用 append 模式写入目标（可改为读出并合并）
            tmp_fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix="._tmp_append_", suffix=".csv")
            os.close(tmp_fd)
            df_to_append.to_csv(tmp_path, index=False, encoding='utf-8-sig', header=False)
            # 使用二进制方式追加临时文件到目标
            with open(path, 'ab') as outf, open(tmp_path, 'rb') as inf:
                shutil.copyfileobj(inf, outf)
                try:
                    outf.flush()
                    os.fsync(outf.fileno())
                except Exception:
                    pass
            os.remove(tmp_path)
            if verbose:
                print("Appended chunk to", path)
            return True, None
        except Exception as e:
            if verbose:
                print("Append error:", e)
            return False, e

    buffer = []
    total_to_process = len(indices) - start_idx
    pbar = tqdm(indices[start_idx:], total=total_to_process, desc="Processing smiles")

    if verbose:
        print("Output CSV path:", out_path)


    for i in pbar:
        smiles = smiles_list[i]
        cid, name, description = fetch_annotation_by_smiles(smiles, verbose=verbose)

        if name or description:
            buffer.append({"CID": cid, "SMILES": smiles, "Name": name, "Description": description})
            processed.add(str(smiles))

        # 周期性保存
        if len(buffer) >= save_every:
            if verbose:
                print(f"About to save {len(buffer)} records to {out_path} (append={os.path.exists(out_path)}, header_needed={header_needed})")
            df_out = pd.DataFrame(buffer)
            ok, err = _append_df_to_csv(out_path, df_out, header_needed)
            if not ok:
                print("Error while saving append:", err, file=sys.stderr)
            else:
                header_needed = False
                if verbose:
                    print(f"Saved {len(buffer)} records to {out_path} (append).")
            buffer = []

        _time.sleep(delay)

    # 保存剩余
    if buffer:
        df_out = pd.DataFrame(buffer)
        ok, err = _append_df_to_csv(out_path, df_out, header_needed)
        if not ok:
            print("Error while saving final chunk:", err, file=sys.stderr)
        else:
            if verbose:
                print(f"Saved final {len(buffer)} records to {out_path}.")

    print("Processing complete. Results saved to:", out_path)
    return out_path