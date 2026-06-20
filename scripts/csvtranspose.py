#!/usr/bin/env python3
import csv
import sys

def transpose_csv():
    reader = csv.reader(sys.stdin)
    rows = list(reader)
    
    if not rows:
        return
    
    # Transpose the data
    max_cols = max(len(row) for row in rows) if rows else 0
    transposed = []
    
    for col_idx in range(max_cols):
        new_row = []
        for row in rows:
            if col_idx < len(row):
                new_row.append(row[col_idx])
            else:
                new_row.append('')
        transposed.append(new_row)
    
    # Write transposed data to stdout
    writer = csv.writer(sys.stdout)
    writer.writerows(transposed)

if __name__ == '__main__':
    transpose_csv()
