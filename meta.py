#encoding: UTF-8

def readmeta(file):
    import pyexiv2
    
    i = pyexiv2.Image(file)
    i.readMetadata()
    
    def item(image, key, value):
        try:
            truevalue = unicode(image[value])
            tmp = image[value]
            if unicode(image[value].__class__) == 'pyexiv2.Rational':
                fvalue = float(tmp.numerator)/tmp.denominator
                if fvalue >= 1:
                    truevalue = "%.1f" % fvalue
            return '<b>%s:</b> %s  ' % (key, truevalue)
        except:
            return ''
    
    d = ''
    d += item(i, 'Date', 'Exif.Photo.DateTimeOriginal')
    d += item(i, 'Camera', 'Exif.Image.Model')
    d += item(i, 'Exposure time', 'Exif.Photo.ExposureTime')
    d += item(i, 'F-number', 'Exif.Photo.FNumber')
    d += item(i, 'ISO rating', 'Exif.Photo.ISOSpeedRatings')
    d += item(i, 'Focal length', 'Exif.Photo.FocalLength')
    try:
        date = i['Exif.Photo.DateTimeOriginal']
    except:
        date = None
    return (d, date)

