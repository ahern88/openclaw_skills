#!/bin/bash
# 周报数据收集脚本
# 用法：bash weekly-collect.sh <输出文件>

OUTPUT_FILE=$1

if [ -z "$OUTPUT_FILE" ]; then
    echo "用法：$0 <输出 JSON 文件>"
    exit 1
fi

WORKSPACE="/home/admin/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"

echo "🔍 开始收集周报数据..."

# 初始化 JSON
echo "{" > "$OUTPUT_FILE"
echo '  "date": "'$(date +%Y-%m-%d)'",' >> "$OUTPUT_FILE"
echo '  "week": "'$(date +%Y-W%V)'",' >> "$OUTPUT_FILE"

# 收集 Memory 文件
echo '  "memory_records": [' >> "$OUTPUT_FILE"
if [ -d "$MEMORY_DIR" ]; then
    first=true
    for file in "$MEMORY_DIR"/*.md; do
        if [ -f "$file" ]; then
            # 读取文件内容（排除标题）
            content=$(cat "$file" | tail -n +2 | head -20)
            filename=$(basename "$file")
            
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$OUTPUT_FILE"
            fi
            
            # 转义 JSON 特殊字符
            content=$(echo "$content" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
            
            echo -n '    {"file": "'$filename'", "content": "'$content'"}' >> "$OUTPUT_FILE"
        fi
    done
fi
echo "" >> "$OUTPUT_FILE"
echo '  ],' >> "$OUTPUT_FILE"

# 收集 Git 提交历史
echo '  "git_commits": [' >> "$OUTPUT_FILE"
if [ -d "$WORKSPACE/.git" ]; then
    cd "$WORKSPACE"
    first=true
    # 获取本周的提交（最近 7 天）
    git log --since="7 days ago" --oneline --no-merges | while read line; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$OUTPUT_FILE"
        fi
        
        # 转义 JSON
        line=$(echo "$line" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
        echo -n '    "'$line'"' >> "$OUTPUT_FILE"
    done
fi
echo "" >> "$OUTPUT_FILE"
echo '  ]' >> "$OUTPUT_FILE"

echo "}" >> "$OUTPUT_FILE"

echo "✅ 数据收集完成：$OUTPUT_FILE"

# 显示统计
memory_count=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
echo "📊 找到 $memory_count 个 memory 文件"

if [ -d "$WORKSPACE/.git" ]; then
    cd "$WORKSPACE"
    git_count=$(git log --since="7 days ago" --oneline | wc -l)
    echo "📊 找到 $git_count 次 git 提交（本周）"
fi
