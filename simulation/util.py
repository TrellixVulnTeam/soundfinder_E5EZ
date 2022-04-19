# standard binary search
def binary_search(arr, low, high, x):
    if (high >= low):
        mid = low + (high - low)//2
        if x == arr[mid]:
            return (mid)
        elif(x > arr[mid]):
            return binary_search(arr, (mid + 1), high, x)
        else:
            return binary_search(arr, low, (mid -1), x)
    return -1
 
 
# num of pairs with diff k in array arr of size n
def count_pairs_diff(arr, n, k):
    count = 0
    arr.sort()
    for i in range (0, n - 2):
        if (binary_search(arr, i + 1, n - 1, arr[i] + k) != -1):
            count += 1
    return count