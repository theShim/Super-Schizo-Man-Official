values = [7/15,3/10,12/25,7/20,3/15]
indices = list(range(len(values)))


print([x+1 for _, x in sorted(zip(values, indices))][::-1]) 