import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from PIL import Image, ImageTk

import os
import glob
import imghdr
import datetime
import sys


# 参照ボタン押下
def refDir_button_pushed():
    # Global宣言(この関数で代入する)
    global last_dir
    
    if last_dir == '':
        iDir = os.path.abspath(os.path.dirname(__file__))
        dirPath = filedialog.askdirectory(initialdir = iDir)
    else:
        dirPath = filedialog.askdirectory(initialdir = last_dir)

    if dirPath:
        # 次に開くパスを設定
        last_dir = dirPath        

        string_entry_dir.set(dirPath)
        # ファイル一覧を渡す(再帰検索なし・ディレクトリ無視)
        fPathList = glob.glob(dirPath + "/*", recursive=False)
        #print(fPathList)
        fileList = [os.path.basename(name) for name in fPathList if os.path.isfile(name) and is_image(name) != None] # 画像ファイルだけ名前抜き出し
        #print(fileList)
        box_list.delete(0, tk.END)
        for name in fileList:
            box_list.insert(tk.END, name)

# 画像ファイルかどうか判別
def is_image(filename):
    try:
        imageType = imghdr.what(filename)
        if imageType != None:
            #print('%s is Image File, Type = %s' % (os.path.basename(filename), str(imageType)))
            pass
        else:
            #print('%s is not Image File...' % os.path.basename(filename))
            pass
        return imageType
    # 起こらないはずだが一応ファイルが無かった場合の例外処理
    except FileNotFoundError as e:
        #print('%s is Not Found...' % os.path.basename(filename))
        print(e)
        return None
    # アクセスできないファイルの場合もケア
    except PermissionError as e:
        #print('%s permission denied...' % os.path.basename(filename))
        print(e)
        return None


# リスト上の画像選択時の処理
def image_selected(event):
    # Global宣言
    global selected_image
    if len(box_list.curselection()) == 1:  # curselection()で選択した画像のインデックスがタプルでとれる
        # 単独選択時はサムネイル画像を表示
        imageFile = Image.open(string_entry_dir.get() + '/' + box_list.get(box_list.curselection()[0]))

        # 横長だったら横を合わせて縦はその比率　逆も然り
        if imageFile.width > imageFile.height * (150/100):
            new_height = int(imageFile.height * (150/imageFile.width))
            imageFile = imageFile.resize((150, new_height))
        else:
            new_width = int(imageFile.width * (100/imageFile.height))
            imageFile = imageFile.resize((new_width, 100))
        # 上下反転にチェックしていた場合は回転
        if True == need_rotate.get():
            imageFile = imageFile.rotate(180)
        # 画像貼り付け
        selected_image = ImageTk.PhotoImage(imageFile)
        canvas_view.create_image(75, 50, image=selected_image)
    else:
        # 複数選択時はデフォルト表示
        canvas_view.create_image(75, 50, image=image_view)


# 画像サイズ(割合)変更時の処理
def rate_changed(*args):
    # 取得した値を整数部分だけの文字列にして表示
    value = '{:.0f}'.format(value_ratio.get())
    #print('ratio = %s' % value)
    display_ratio.set(value + '%')


# 画像圧縮方法選択時の処理
def algo_selected(event):
    # Global宣言
    global selected_algo

    if string_algo.get()   == 'NEAREST':  selected_algo = Image.NEAREST
    elif string_algo.get() == 'BOX':      selected_algo = Image.BOX
    elif string_algo.get() == 'BILINEAR': selected_algo = Image.BILINEAR
    elif string_algo.get() == 'HAMMING':  selected_algo = Image.HAMMING
    elif string_algo.get() == 'BICUBIC':  selected_algo = Image.BICUBIC
    elif string_algo.get() == 'LANCZOS':  selected_algo = Image.LANCZOS
    else: selected_algo = Image.NEAREST  # とりあえず設定
    #print('algorithm no. = %d' % selected_algo)


# 実行ボタン押下
def exec_button_pushed():
    # 何も選択されていなかったらダイアログ表示
    if len(box_list.curselection()) == 0:
        messagebox.showinfo('No files selected', u'ファイルが選択されていません。')
        return

    # 選択されている画像のリストを取得
    fileList = []
    for index in box_list.curselection():
        fileList.append('%s/%s' % (string_entry_dir.get(), box_list.get(index)))

    # 処理実行
    # 圧縮方法が選択されていなかったらダイアログ表示
    if algo_resize.get() == '---select---':
        messagebox.showinfo('Algorithm not selected', u'圧縮方法が選択されていません。')
        return
    else:
        # 出力先フォルダを生成(日付+変更率)
        try:
            output_directory = ('%s/resize_%s_%s' % (string_entry_dir.get(), datetime.datetime.now().strftime('%Y%m%d%H%M%S'), display_ratio.get()))
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)
                print('Make Dirctory: %s' % output_directory)
        # アクセスできない場合はエラー終了
        except PermissionError as e:
            #print('%s permission denied...' % os.path.basename(filename))
            print(e)
            messagebox.showinfo('Failed...', u'ディレクトリが作成できませんでした。\n出力先:%s' % output_directory)
            return None

        # 順次処理して出力フォルダに保存していく
        save_error = False
        for f in fileList:
            img = Image.open(f)
            img_resize = img.resize((int(img.width * (value_ratio.get()/100)), int(img.height * (value_ratio.get()/100))))
            # 上下反転にチェックしていた場合は回転
            if True == need_rotate.get():
                img_resize = img_resize.rotate(180)
            fdir, ffile = os.path.split(f)
            fname, fext = os.path.splitext(ffile)
            # たまに例外になる画像があるので拾う
            try:
                img_resize.save('%s/%s_resize%s' % (output_directory, fname, fext))
            except ValueError as e:
                print('%s cannot be edited... %s' % (ffile, e))
                save_error = True
                pass
            except IOError as e:
                print('%s cannot be edited... %s' % (ffile, e))
                save_error = True
                pass
        if save_error == True:
            messagebox.showinfo('Finish', u'処理が終わりましたが一部出力されませんでした。\n出力先:%s' % output_directory)           
        else:
            messagebox.showinfo('Finish', u'処理が終わりました。\n出力先:%s' % output_directory)

# メニューからの終了処理
def close_application():
    win.destroy()
    sys.exit(0)

# 画像リソースへアクセスするための関数
def rc_path(filename):
  if hasattr(sys, "_MEIPASS"):
      return os.path.join(sys._MEIPASS, filename)
  return os.path.join(filename)


# 各種ウィジェット作成・配置
def create_widget(win):
    # Global宣言
    global string_label_dir
    global string_entry_dir
    global last_dir
    global string_list
    global canvas_view
    global image_view
    global value_ratio
    global display_ratio
    global string_algo
    global label_ratio_str
    global label_algo_str
    global algo_resize
    global bg_image
    global box_list
    global need_rotate

    # 各フレームの座標定義
    frame_pos = {
        'pos_dir'    : (0, 0),
        'pos_list'   : (10, 50),
        'pos_view'   : (310, 50),
        'pos_resize' : (310, 170)
        }

    # ウィンドウサイズ指定・背景画像を用意
    # ウィンドウサイズは画像サイズにあわせる　500x300あればよいが無い場合はリサイズ
    try:
        bg_imageFile = Image.open(rc_path('img/bg.jpg'))
        if bg_imageFile.width > 500:
            if bg_imageFile.height > 300:
                win.geometry('%sx%s' % (bg_imageFile.width, bg_imageFile.height))
                #print('case1:%sx%s' % (bg_imageFile.width, bg_imageFile.height))
            else:
                bg_imageFile = bg_imageFile.resize((int(bg_imageFile.width*(300/bg_imageFile.height)), 300))
                win.geometry('%sx%s' % (bg_imageFile.width, 300))
                #print('case2: %sx%s' % (bg_imageFile.width, 300))
        elif bg_imageFile.height > 300:
            bg_imageFile = bg_imageFile.resize((500, int(bg_imageFile.height*(500/bg_imageFile.width))))
            win.geometry('%sx%s' % (500, bg_imageFile.height))
            #print('case3:%sx%s' % (500, bg_imageFile.height))
        else:
            bg_imageFile = bg_imageFile.resize((500, 300))
            win.geometry('%sx%s' % (500, 300))
            #print('case4:%sx%s' % (500, 300))

    except FileNotFoundError as e:
        # 背景画像が無い場合は緑の背景にする
        print(e)
        bg_imageFile = Image.new('RGB', (500, 300), '#325050')
        win.geometry('%sx%s' % (500, 300))
        
    bg_image = ImageTk.PhotoImage(bg_imageFile)        
    bg_bg = tk.Label(win, image=bg_image).place(x=0, y=0)

    # メニューバー
    menu_bar = tk.Menu(win)
    win.config(menu = menu_bar)
    menu_file = tk.Menu(menu_bar, tearoff=0)
    menu_file.add_command(label = '終了', command=close_application)
    menu_bar.add_cascade(label = 'ファイル', menu = menu_file)

    # ===================================================================
    # 上部フレーム:ディレクトリ参照部分
    frame_dir = ttk.Frame(win, width=500, height=50, padding=0)
    frame_dir.place(x=frame_pos['pos_dir'][0], y=frame_pos['pos_dir'][1])

    # 背景画像を貼る(フレームの配置座標ではなくwinの0,0からになるように)
    bg_dir = tk.Label(frame_dir, image=bg_image).place(x=(-1)*(frame_pos['pos_dir'][0]), y=(-1)*(frame_pos['pos_dir'][1]))

    # 各種パーツ類
    string_label_dir = tk.StringVar()
    string_entry_dir = tk.StringVar()
    string_label_dir.set('ディレクトリ: ')
    label_dir = tk.Label(frame_dir, textvariable=string_label_dir, fg='white', bg='#2F4F4F').place(x=5, y=5)
    entry_dir = tk.Entry(frame_dir, textvariable=string_entry_dir, width=50)
    entry_dir.place(x=80, y=5)
    entry_dir.configure(state='readonly')
    button_dir = tk.Button(frame_dir, text='参照', command=refDir_button_pushed, fg='white', bg='#2F4F4F').place(x=400, y=5)
    last_dir = ''
    
    # ===================================================================
    # 下部左側フレーム:ファイルリスト表示部分
    frame_list = ttk.Frame(win)
    frame_list.place(x=frame_pos['pos_list'][0], y=frame_pos['pos_list'][1])

    # 各種パーツ類
    string_list = tk.StringVar()

    box_list = tk.Listbox(frame_list, listvariable=string_list, width=45, height=15, selectmode = 'extended')
    box_list.bind('<<ListboxSelect>>', image_selected)
    box_list.grid(row=0, column=0)
    scroll_list = tk.Scrollbar(frame_list, orient=tk.VERTICAL, command=box_list.yview)
    scroll_list.grid(row=0, column=1, sticky=(tk.N, tk.S))
    box_list.configure(yscrollcommand = scroll_list.set)

    # ===================================================================
    # 下部右側上フレーム:画像表示部分
    frame_view = ttk.Frame(win)
    frame_view.place(x=frame_pos['pos_view'][0], y=frame_pos['pos_view'][1])

    # 各種パーツ類
    canvas_view = tk.Canvas(frame_view, width=150, height=100)
    canvas_view.grid()

    imageFile = Image.new('RGB', (160, 110), (50, 50, 50))
    image_view = ImageTk.PhotoImage(imageFile)
    canvas_view.create_image(75, 50, image=image_view)

    # ===================================================================
    # 下部右側下フレーム:処理実施部分
    frame_resize = ttk.Frame(win)
    frame_resize.place(x=frame_pos['pos_resize'][0], y=frame_pos['pos_resize'][1])

    # 背景画像を貼る(フレームの配置座標ではなくwinの0,0からになるように)
    bg_resize = tk.Label(frame_resize, image=bg_image).place(x=(-1)*(frame_pos['pos_resize'][0]), y=(-1)*(frame_pos['pos_resize'][1]))

    # 各種パーツ類
    value_ratio = tk.DoubleVar()
    value_ratio.trace('w', rate_changed)
    display_ratio = tk.StringVar()

    label_ratio_str = tk.StringVar()
    label_ratio_str.set('倍率: ')
    label_ratio = tk.Label(frame_resize, textvariable=label_ratio_str, fg='white', bg='#2F4F4F').grid(row=0, column=0, sticky=(tk.W))
    
    scale_resize =ttk.Scale(frame_resize, variable=value_ratio, orient=tk.HORIZONTAL, length=150, from_=1, to=300)
    scale_resize.set(100)
    scale_resize.grid(row=1, column=0, columnspan=2, sticky=(tk.N,tk.E,tk.S,tk.W))

    entry_resize = tk.Entry(frame_resize, textvariable=display_ratio, width=5)
    entry_resize.grid(row=1, column=1, sticky=(tk.E))
    entry_resize.configure(state='readonly')

    label_algo_str = tk.StringVar()
    label_algo_str.set('圧縮アルゴリズム: ')
    label_algo = tk.Label(frame_resize, textvariable=label_algo_str, fg='white', bg='#2F4F4F').grid(row=2, column=0, sticky=(tk.W))
    
    string_algo = tk.StringVar()
    algo_resize = ttk.Combobox(frame_resize, textvariable=string_algo)
    algo_resize.bind('<<ComboboxSelected>>', algo_selected)
    algo_resize['values']=('NEAREST', 'BOX', 'BILINEAR', 'HAMMING', 'BICUBIC', 'LANCZOS')
    algo_resize.set('---select---')
    algo_resize.grid(row=3, column=0, columnspan=2, sticky=(tk.N,tk.E,tk.S,tk.W))

    exec_resize = tk.Button(frame_resize, text='実行', command=exec_button_pushed, fg='white', bg='#2F4F4F').grid(row=4, column=0, sticky=(tk.W))

    need_rotate = tk.BooleanVar()
    need_rotate.set(False)
    check_rotate = tk.Checkbutton(frame_resize, text='上下回転', variable=need_rotate)
    check_rotate.grid(row=4, column=1, sticky=(tk.W))

    # ===================================================================


if __name__ == '__main__':
    win = tk.Tk()
    win.title('Green Panda File Resizer')
    win.resizable(width=False, height=False)
    create_widget(win)
    win.mainloop()

