from GlobalFunc import read_txt

path = "E:/0/学习/实习/2025.8.12/page_66.txt"
lines = read_txt(path)
for line in lines:
    suffix = line.split('：')[-1]
    print(suffix)
