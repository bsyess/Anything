#include<iostream>
using namespace std;
class Dog
{
	private:
		string name,sex,age;
		
		double weight;
	public:
		Dog(string name,int age,string sex,double weight)
		{
			this->name=name;
			this->age=age+'0';
			if(age==1)
			{
				this->age=this->age+" year old.";
			}
			else this->age=this->age+" years old.";
			if(sex=="m")
			{
				this->sex="male";
			}
			
			this->weight=weight;
		}
		void show()
		{
			cout<<"It is my dog."<<endl;
			cout<<"Its name is "<<name<<"."<<endl;
			cout<<"It is "<<age<<endl;
			cout<<"It is "
			cout<<"It is "<<weight<<" kg.";	
		}

 };
 int main()
 {
 	string name,sex;
 	int age;
 	double weight;
 	cin>>name>>age>>sex>>weight;
 	Dog d(name,age,sex,weight);
 	d.show();
 	return 0;
 	
 	
 }
 
 
 
  
