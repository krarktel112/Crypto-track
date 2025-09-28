rate = input("Rate: ") or 0
ot = int(rate)*1.5
hours = input("Hours: ") or 0
minutes = input("Minutes: ") or 0
minutes = int(minutes) / 60
hours = int(hours) + int(minutes)
if hours <= 40:
  gross = int(hours) * int(rate)
elif hours > 40:
  gross1 = 40 * int(rate)
  gross2 = (int(hours)-40)*int(ot)
  gross = int(gross1) + int(gross2)
else:
  print("Error")

print(int(gross)-49.84-((int(gross)-49.84)*(0.084+0.03+0.0159+0.0145+0.062))-13.75)
