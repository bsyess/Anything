#include<iostream>
#include<cstring>
using namespace std;
class Person
{
	private:
	    string name;
		int age;
		char sex;
	public:
	    void Register(string name,int ag,char se);
		void showme();
	
};
void Person::Register(string na,int ag,char se)
{
	name=na;
	age=ag;
	sex=se;
}
void Person::showme()
{
	cout<<name<<' '<<age<<' '<<sex;
}
int main()
{
	Person per1,per2;
	char sex;
	string name;
	int age;
	cin>>name>>age>>sex;
	per1.Register(name,age,sex);
	per1.showme();
	cout<<endl;
	per2.Register("Zhang3",19,'m');
	per2.showme();
	
	return 0;
}

