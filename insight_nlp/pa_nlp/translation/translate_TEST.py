import pa_nlp.translation.translate as Trans

if __name__ == '__main__':
  src = "Beijing"
  tran = Trans.translate_sentence(src)
  print(f"{src} --> {tran}")
  
  src = "你好，平安银行"
  tran = Trans.translate_sentence(src, "en")
  print(f"{src} --> {tran}")
  
