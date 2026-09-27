# MultiTranslat
多次翻译文本，让文本失真。

## 先设置模型
复制 models/model.json.example 到 models/model.json
修改 models/model.json 中的 api_key, base_url, model 为你自己的模型信息

## 自定义模型
在 models 目录下添加一个 json 文件 文件名就是模型的别名等, 随便设, 比如 `deepseek.json` 
修改文件内容就是模型的配置信息. 参考 models/model.json.example

## 用法
<>包裹的为必须, []包裹的为可选
```shell
python multiTranslat.py "文本" [ -s 原本语言 ] [ -t 目标语言 ] [ -c 翻译次数 ]
```