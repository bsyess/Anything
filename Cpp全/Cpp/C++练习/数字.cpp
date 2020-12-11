#include<iostream>
using namespace std;
int raoxing(int *a,int n,int m,int k) 
{
	int i,j;
	
	for(i=m;i<n-m-1;i++)
	{
		a[i*n+m]=k;
		k++;
	}
	for(i=m;i<n-m;i++)
	{
		a[(n-m-1)*n+i]=k;
		k++;
	}
	for(i=n-m-1;i>=m;i--)
	{
		a[((i+m)*n+m)]=k;
		k++;
	}
	for(i=n-m-1;i>=m;i--)
	{
		a[(n-m-1)*n+i]=k;
		k++;
	}
	if(m<n)
	{
		return raoxing(a,n,m+1,k);
	}
	return k;
}
int main()
{
	int a[100];
	int n;
	int i,j;
	cin>>n;
	for(i=0;i<n;i++)
	{
		for(j=0;j<n;j++)
		{
			a[i*n+j]=0;
		}
	}
	
	
	int k=1,m=0;
	int x; 
	x=raoxing(a,n,m,k);
	
	for(i=0;i<n;i++)
	{
		for(j=0;j<n;j++)
		{
			if(a[i*n+j]<10)
			cout<<0;
			
			cout<<a[i*n+j]<<' ';
		}
		cout<<endl;	
	}
	cout<<x;
	return 0;
}
