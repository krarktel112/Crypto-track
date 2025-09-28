rate = input("Rate: ") or 0
ot = int(rate)*1.5
hours = input("Hours: ") or 0
minutes = input("Minutes: ") or 0
minutes = int(minutes) / 60
hours = hours + minutes 
if hours <= 40:
  gross = hours * rate
elif hours > 40:
  gross1 = 40 * rate
  gross2 = (hours-40)*ot
  gross = gross1 + gross2
else:
  print("Error")

print(gross-49.84-((gross-49.84)*(0.084+0.03+0.0159+0.0145+0.062))-13.75)
