import difflib

def compare_texts(text1, text2):
    return difflib.HtmlDiff().make_file(
        text1.splitlines(),
        text2.splitlines(),
        fromdesc="Документ 1",
        todesc="Документ 2"
    )
