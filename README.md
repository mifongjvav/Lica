# Lica

使用json来存储文件，而不是zip

## 用法

```python

# 打包
python Main.py pack zip文件 保存的文件名，默认无后缀

# 解包
python Main.py unpack lica文件 输出文件夹

# 解包超大文件（需安装 ijson）
pip install ijson
python Main.py unpack lica文件 输出文件夹 --stream

```
