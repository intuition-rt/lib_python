import ilo

ilo.info()


#ilo.check_ilo_on_network()

my_ilo = ilo.robot(1)

print (my_ilo.ID)