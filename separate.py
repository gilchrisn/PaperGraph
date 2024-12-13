#python script that takes in results2.txt, and separates content into separate files that contains no more than 5000 characters

import os

def split_file(input_file, output_dir, max_chars=5000):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, 'r') as file:
        content = file.read()

    part = 1
    start = 0
    while start < len(content):
        end = start + max_chars
        chunk = content[start:end]

        output_file = os.path.join(output_dir, f"part_{part}.txt")
        with open(output_file, 'w') as out_file:
            out_file.write(chunk)

        part += 1
        start = end

if __name__ == "__main__":
    input_file = "results2.txt"
    output_dir = "separated_files"
    split_file(input_file, output_dir)