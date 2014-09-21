oldpagerange = 'Showing images: [0-3]'
temp1 = oldpagerange.split('Showing images: [')[1]
print temp1
temp2 = temp1.split('-')
print temp2
start = temp2[0]
end = temp2[1].split(']')[0]

print start
print end
