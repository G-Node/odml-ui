
try:
    from gi import pygtkcompat
    pygtkcompat.enable()
    pygtkcompat.enable_gtk(version='3.0')
    import gtk
    import gobject

except Exception as e:
    print(e)
    exit(0)
