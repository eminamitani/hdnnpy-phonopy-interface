import h5py
import matplotlib.pyplot as plt
import glob


flist=glob.glob("kappa*.hdf5")
print(flist)

for fhdf in flist:
    f=h5py.File(fhdf)
    mesh=fhdf.lstrip("kappa-m").rstrip(".hdf5")
    print(mesh)
    print(list(f))

    print(f['kappa'].shape)
    kxx=f['kappa'][:,0]
    kyy=f['kappa'][:,1]
    kzz=f['kappa'][:,2]

    temp=f['temperature']

    #write down to txt file
    with open("data"+mesh+".dat", 'w') as data:
        data.write("# temperature(K)  xx-component (W/mK)  yy-component (W/mK) zz-component (W/mK) \n")
        for i in range(len(temp)):
            data.write(str(temp[i]) + "  " +str(kxx[i]) + "  " + str(kyy[i]) +"  "+ str(kzz[i]) +"\n")


    plt.figure(figsize=(12,5), dpi=120)
    plt.subplots_adjust(wspace=0.5)

    plt.subplot(131)
    plt.xlabel("temperature (K)")
    plt.ylabel("thermal conductivity (W/mK)")
    plt.title("xx component")
    plt.xlim([100,800])
    plt.ylim([0,1000])
    plt.plot(temp,kxx)

    plt.subplot(132)
    plt.xlabel("temperature (K)")
    plt.ylabel("thermal conductivity (W/mK)")
    plt.title("yy component")
    plt.xlim([100,800])
    plt.ylim([0,1000])
    plt.plot(temp,kyy)

    plt.subplot(133)
    plt.xlabel("temperature (K)")
    plt.ylabel("thermal conductivity (W/mK)")
    plt.title("zz component")
    plt.xlim([100,800])
    plt.ylim([0,1000])
    plt.plot(temp,kzz)

    plotfile="kappa"+mesh+".png"
    plt.savefig(plotfile)
    plt.show()
