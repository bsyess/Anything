#include<iostream>
using namespace std;
int main()
{
	
	
	int i,f3fenzi=120,f3fenmu=240;
	for(i=2;i<=f3fenmu/2;i++)
	{
		if(f3fenmu%i==0&&f3fenzi%i==0)
		{
			f3fenmu=f3fenmu/i;
			f3fenzi=f3fenzi/i;
			i=1;
			if(f3fenmu==1)
			{
				break;
			}
		}
		if(f3fenmu==1) break;
	}
	if(f3fenzi%f3fenmu==0)
	{
		f3fenmu=1;
		f3fenzi=f3fenzi/f3fenmu;
	}
	
	cout<<f3fenzi<<' '<<f3fenmu;
	
	
	
}


