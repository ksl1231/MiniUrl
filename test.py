import get

if __name__ == '__main__':
    URL = 'http://e0.ifengimg.com/12/2018/1124/F427FD93A0A1202EDF6CEA8F301065CE16FC6EBE_size25_w395_h517.jpeg'
    # URL = 'http://cycy.198424.com/first_blood_gaming_mouse_driver.zip'
    filename = '1.jpg'
    get.loadurl(URL,filename=filename, retries=2)