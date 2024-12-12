# Phan dinh nghia ham o day
a = 0
def changeme():
    global a
    a = a + 2
    return
changeme()
print("Cac gia tri ben ngoai ham la: ", a)