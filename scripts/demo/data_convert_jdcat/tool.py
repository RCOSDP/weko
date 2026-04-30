import csv
import argparse


def replace_text(input_file, output_file, csv_file):

    # 置換ルール読み込み
    rules = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            before, after = row
            rules.append((before, after))

    # 入力ファイル読み込み
    with open(input_file, encoding="utf-8") as f:
        text = f.read()

    # 置換処理
    for before, after in rules:
        text = text.replace(before, after)

    # 出力
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    parser = argparse.ArgumentParser(description="CSVに基づく文字列置換ツール")

    parser.add_argument("input_file", help="入力ファイル")
    parser.add_argument("output_file", help="出力ファイル")
    parser.add_argument("csv_file", help="置換ルールCSV")

    args = parser.parse_args()

    replace_text(args.input_file, args.output_file, args.csv_file)


if __name__ == "__main__":
    main()