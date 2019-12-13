import itertools

start_fill = "<:pb_l_f:654497886326882324>"
start_empty = "<:pb_l_e:654497886314299402>"
center_fill = "<:pb_c_f_{}:654497885416587266>"
center_empty = "<:pb_c_e_{}:654497885739548672>"
end_fill = "<:pb_r_f:654497709176389634>"
end_empty = "<:pb_r_e:654497708630867999>"

def create(end=100, x_per=10, value=30):
    bar = ""
        
    if x_per > end:
        raise ValueError("'x_per' can not be higher than 'end value'!")

    if value > end:
        raise ValueError("'value' can not be higher than 'end value'!")

    total = int((end/x_per))
    total_filled = int(value/x_per)
    total_empty = int(total-total_filled)


    if total_filled == 0:
        bar += start_empty
    else:
        bar += start_fill

    if total_filled != total:
        total_center_fill = total_filled -1
    else:
        total_center_fill = total_filled

    if total_center_fill > 0:
        for x in list(itertools.islice(itertools.cycle([1, 2]), total_center_fill)):
            bar += center_fill.format(x)

    if total_empty >= 1:
        if total_empty == 1:
            total_center_empty = total_empty -1
        else:
            total_center_empty = total_empty
        for x in list(itertools.islice(itertools.cycle([1, 2]), total_center_empty)):
            bar += center_empty.format(x)

    if total_empty >= 1:
        bar += end_empty
    if total_empty == 0:
        bar += end_fill

    return bar

