#---------------------------插值法集合
def NMI(new_image, new_i, new_j, A, B, C, D):
    new_image[new_i, new_j] = A  # C(0, 0)
    new_image[new_i, new_j + 1] = (A + B) // 2  # C(0, 1)
    new_image[new_i + 1, new_j] = (A + C) // 2  # C(1, 0)
    new_image[new_i + 1, new_j + 1] = (A + B + C) // 3  # C(1, 1)

def INP(new_image, new_i, new_j, A, B, C, D):
    new_image[new_i, new_j] =  A
    new_image[new_i, new_j + 1] = (A+((A + B)/2)) //2
    new_image[new_i + 1, new_j] = (A+((A + C)/2)) //2
    new_image[new_i + 1, new_j + 1] = (((A+((A + B)/2)) //2) + ((A+((A + C)/2)) //2)) //2

def ENMI(new_image, new_i, new_j, A, B, C, D):
    new_image[new_i, new_j] = A
    new_image[new_i,new_j +1] = (A + B)//2
    new_image[new_i  +1,new_j] = (A + C)//2
    new_image[new_i + 1, new_j + 1] = (A+B+C+D)//4

def NIE(new_image, new_i, new_j, A, B, C, D):
    new_image[new_i, new_j] = A
    new_image[new_i,new_j +1] = (((A+B)//3) + (C+D))//6
    new_image[new_i + 1,new_j] = (((A+C)//3) + (B+D))//6
    new_image[new_i + 1, new_j + 1] = (A+B+C+D)//4

def ENMI(new_image, new_i, new_j, A, B, C, D):
    new_image[new_i, new_j] = A  # C(0, 0)
    new_image[new_i, new_j + 1] = (A + B) // 2  # C(0, 1)
    new_image[new_i + 1, new_j] = (A + C) // 2  # C(1, 0)
    new_image[new_i + 1, new_j + 1] = (A + B + C + D) // 4  # C(1, 1)

def MNMI(new_image, new_i, new_j, A, B, C, D):
    new_image[new_i, new_j] = A  # C(0, 0)
    new_image[new_i, new_j + 1] = (2*A + 2*B +((A + B + C + D) // 4)) // 5  # C(0, 1)
    new_image[new_i + 1, new_j] = (2*A + 2*C +((A + B + C + D) // 4)) // 5  # C(1, 0)
    new_image[new_i + 1, new_j + 1] = (A + B + C + D) // 4  # C(1, 1)   