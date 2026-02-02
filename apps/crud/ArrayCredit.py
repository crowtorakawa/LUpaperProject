# cube_label.py
import numpy as np

def create_labeled_matrix(size_N=(256, 256, 256), size_n=(4, 4, 4)):
    """
    建立壓縮版與展開版的立方體編號矩陣

    size_N: 原矩陣大小
    size_n: 子立方體大小
    return: (labeled_matrix_compressed, labeled_matrix)
    """

    # 創建一個 256 x 256 x 256 的 3D 矩陣
    matrix = np.zeros(size_N, dtype=int)

    # 獲取分割後每個維度的子立方體數量
    num_subcubes = tuple(size_N[i] // size_n[i] for i in range(3))
    # num_subcubes = (
    #     size_N[0] // size_n[0],
    #     size_N[1] // size_n[1],
    #     size_N[2] // size_n[2]
    # )

    # 初始化一個新的較小的矩陣來存儲每個小立方體的編號
    labeled_matrix_compressed = np.zeros(num_subcubes, dtype=int)

    cube_id = 1
    for i in range(num_subcubes[0]):
        for j in range(num_subcubes[1]):
            for k in range(num_subcubes[2]):
                labeled_matrix_compressed[i, j, k] = cube_id
                cube_id += 1
    half_z = size_n[2] // 2
    total_vals = size_n[0] * size_n[1] * half_z
    numbers = np.arange((size_n[0] * size_n[1] * size_n[2]/2))
    print(numbers)
    np.random.shuffle(numbers)
    print(numbers)
    for i in range(0, size_N[2], size_n[2]):  # z
        for j in range(0, size_N[1], size_n[1]):  # y
            for k in range(0, size_N[0], size_n[0]):  # x
            
                # 生成兩份不同的亂數序列
                nums1 = numbers.copy()
                nums2 = numbers.copy()
                np.random.shuffle(nums1)
                np.random.shuffle(nums2)
                
                # 填上半
                matrix[i:i+half_z, j:j+size_n[1], k:k+size_n[0]] = nums1.reshape(half_z, size_n[1], size_n[0])
                # 填下半
                matrix[i+half_z:i+size_n[2], j:j+size_n[1], k:k+size_n[0]] = nums2.reshape(half_z, size_n[1], size_n[0])            
                

    return labeled_matrix_compressed,matrix
def check_duplicates(matrix, z_start, z_end):
    check = []
    dup_count = 0
    for z in range(z_start, z_end):
        for y in range(4):
            for x in range(4):
                val = matrix[z, y, x]
                if val not in check:
                    check.append(val)
                else:
                    print(f"重複: {val}")
                    dup_count += 1
    return dup_count


def output_matrix():
    labeled_matrix_compressed, matrix =  create_labeled_matrix()
    print(labeled_matrix_compressed[:4, :4, :4])
    print("最後一個立方體編號:", labeled_matrix_compressed[-1, -1, -1])
    print(f"總共分割成 {labeled_matrix_compressed.size} 個子立方體")
    print(matrix[:4, :4, :4])
    xxx = 0
    xxx += check_duplicates(matrix, 0, 2)  # 上半
    xxx += check_duplicates(matrix, 2, 4)  # 下半
    print("總重複數:", xxx)



    if(xxx == 0):
        np.save("3Dmatrix.npy",matrix) 
        return labeled_matrix_compressed, matrix
    else:
        print('generate fail')
        
# 測試用
if __name__ == "__main__":
    # 測試用
   labeled_matrix_compressed, matrix = output_matrix()
   print(labeled_matrix_compressed.size, matrix.size)
    
