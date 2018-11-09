/**
 *  Copyright (c) 2017 Dubray Alexandre 
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package src.librairies;

import static student.Translations.Translator._;

import java.text.MessageFormat;

import java.util.Arrays;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Field;
import java.lang.reflect.Type;
import java.lang.reflect.Modifier;

import java.lang.IllegalAccessException;
import java.lang.NoSuchFieldException;
import java.lang.reflect.InvocationTargetException;
import java.lang.IllegalArgumentException;
import java.lang.InstantiationException;
import java.lang.ExceptionInInitializerError;

import java.util.List;
import java.util.ArrayList;

/**
 * Classe java contenant des fonctions pour faire de la réflection sur une classe
 * @version aout 2017
 */

public class Inspector {

	@SuppressWarnings("unchecked")
	/**
	 * Cette méthode permet de créer une instance de la classe c sans être 
	 * certain que le constructeur voulu existe. Le constructeur recherché
	 * doit être public et les paramètre dans param doivent être dans l'ordre
	 * de la déclaration du constructeur
	 * 
	 * @pre		c != null, param != null
	 * @post	Si un constructeur est trouvé, retourne une instance de 
	 *			la classe, null sinon.
	 */
	public static Object run_construct(Class c,Object [] param) {
		try {
			Class [] paramType = new Class[param.length];
			for(int i=0;i<paramType.length;i++)
				paramType[i] = param[i].getClass();
			Constructor ctor = c.getConstructor(paramType);
			return ctor.newInstance(param);
		} catch (NoSuchMethodException e) {
			return null;
		} catch (InstantiationException e) {
			return null;
		} catch (IllegalAccessException e) {
			return null;
		} catch ( IllegalArgumentException e){
			return null;
		} catch (InvocationTargetException e) {
			return null;
		} catch (ExceptionInInitializerError e) {
			return null;
		}
	}

	/**
	 * Cette méthode permet d'appeler une méthode de l'instance instance 
	 * de la classe instance.getClass() sans être sur que la méthode est définie dans la classe.
	 *
	 * @pre		instance != null, fun_name != null
	 * @post	Si la méthode est bien définie dans la classe, retourne le résultat de l'appel de méthode.
	 *			Sinon, une NoSuchMethodException est lancée
	 */
	public static Object run_method(Object instance,String fun_name, Object [] param) throws NoSuchMethodException{
		try {
			Class [] classes = new Class[param.length];
			for(int i=0;i<param.length;i++)
				classes[i] = param[i].getClass();
			Method m = instance.getClass().getDeclaredMethod(fun_name,classes);
			boolean initialAccess = m.isAccessible();
			m.setAccessible(true);
			Object ret = m.invoke(instance,param);
			m.setAccessible(initialAccess);
			return ret;
			/* Need to better handle exceptions */
		} catch (IllegalAccessException e) {
			return null;
		} catch (IllegalArgumentException e) {
			return null;
		} catch (InvocationTargetException e) {
			return null;
		}
	}

	/**
	 *
	 * Cette méthode permet de vérifier si un ensemble de constructeur sont présent dans la classe. Chaque constructeur
	 * est définis de la manière suivante :
	 *		- Le i-ème constructeur a comme modificateur expected_modifier[i]
	 *		- Le i-ème constructeur a comme type de paramètre expected_param[i]
	 *		- Le i-ème constructeur ''throws'' comme type d'exception expected_exception[i]
	 *
	 *	Notons que la vérification peut se faire sans comparer les modificateurs et les exception 
	 *	en passant null aux paramètres assciés.
	 *
	 * @pre		expected_modifier.length (si != null) == expected_param.length == expected_exception.length (si != null), c != null
	 *			pour 0 < i < expected_param.length : expected_param[i] != null,
	 *			pour 0 < i < expected_exception : expected_exception[i] != null
	 *			pour 0 < i < j < expected_modifier.length : expected_param[i] != expected_param[j]
	 *			
	 * @post	Vérifie que les constructeur définit par les tableaux expected_modifier, expected_param et expected_exception 
	 *			sont présent dans la classe c. Le tableau des messages d'erreur (potentiellement null) est renvoyé
	 */
	public static String [] inspect_constructors(Class c, int [] expected_modifier, Class [][] expected_param, Class [][] expected_exception) {
		String [] error = new String [expected_param.length];
		for(int i=0;i<error.length;i++)
			error[i] = check_constructor(c,(expected_modifier != null) ? expected_modifier[i] : -1,expected_param[i],(expected_exception != null) ? expected_exception[i] : null);
		return error;
	}

	/**
	 * Cette méthode va checher dans la classe c un constructeur qui répond aux critère suivant :
	 *		- Le modificateur de visibilité est expected_modifier
	 *		- Le nombre de paramètre est expected_param.length
	 *		- Le tableau des types du paramètre est une permutation de expected_param
	 *		- Le nombre d'exception déclarée "throws" par le constructeur est expected_exception.length
	 *		- Chaque exception lancée par le constructeur se trouve dans expected_exception
	 *
	 * @pre		c != null ,
	 *			expected_modifier = Modifier.PRIVATE | Modifier.PUBLIC | Modifier.PROTECTED,
	 *			expected_param != null,
	 *			expected_exception != null ,
	 *			chaque exception dans expected_exception apparait une seule fois dans le tableau
	 *
	 * @post	Cherche un constructeur suivant les contraintes énoncée plus haut. Si aucun constructeur respectant
	 *			l'ensemble des contrainte n'as été trouvé, un message d'erreur est renvoyer. Si le constructeur est
	 *			trouvé, la méthode renvoie null
	 */
	private static String check_constructor(Class c,int expected_modifier, Class [] expected_param, Class [] expected_exception) {

		/* Récupération des constructeurs */
		Constructor [] allConstructors = c.getDeclaredConstructors();
		for(Constructor construct : allConstructors) {
			if(check_modifiers(construct.getModifiers(),expected_modifier)) {
				if(check_param(construct.getParameterTypes(),expected_param)) {
					if(check_exception(construct.getExceptionTypes(),expected_exception)) {
						return null;
					}
				}
			}
		}
		String error_msg;
		String feed;
		if(expected_modifier != -1 && expected_exception != null){
			error_msg = _("Le constructeur avec comme modificateur [{0}], comme types d''arguments {1} et comme exceptions déclarée via throws {2} n''as pas été trouvé !");
			feed = MessageFormat.format(error_msg,Modifier.toString(expected_modifier),Arrays.toString(expected_param),Arrays.toString(expected_exception));
		}
		else if(expected_modifier != -1 && expected_exception == null) {
			error_msg = _("Le constructeur avec comme modificateur [{0}], comme types d''arguments {1} n''as pas été trouvé !");
			feed = MessageFormat.format(error_msg,Modifier.toString(expected_modifier),Arrays.toString(expected_param));
		} else if (expected_modifier == -1 && expected_exception != null) {
			error_msg = _("Le constructeur avec comme types d''arguments {0} et comme exceptions déclarée via throws {1} n''as pas été trouvé !");
			feed = MessageFormat.format(error_msg,Arrays.toString(expected_param),Arrays.toString(expected_exception));
		} else {
			error_msg = _("Le constructeur avec comme types d''arguments {0} n''as pas été trouvé !");
			feed = MessageFormat.format(error_msg,Arrays.toString(expected_param));
		} 
		return feed;
	}

	/**
	 * Cette méthode permet de vérifier si un ensemble de méthodes sont présentes dans la classe. Les méthodes à vérifier
	 * sont définies comme suit : 
	 *		- La i-ème méthode a comme nom name[i]
	 *		- La i-ème méthode a comme type de retour return_type[i]
	 *		- La i-ème méthode a comme modificateur modifier[i]
	 *		- La i-ème méthode a comme types de paramètres expected_param[i]
	 *		- La i-ème méthode a comme type d'exception "throws" expected_exception[i]
	 *
	 *	Notons que la vérification peut se faire sans comparer les modificateurs et les exception 
	 *	en passant null aux paramètres assciés.
	 *
	 * @pre		name != null , return_type != null, Class != null
	 *			modifier.length (si != null) == return_type.length == name.length == expected_param.length == expected_exception.length (si != null)
	 *			expected_param != null et pour 0 < i < expected_param.length : expected_param[i] != null,
	 *			expected_exception != null => pour 0 < i < expected_exception.length : expected_exception[i] != null,
	 *
	 * @post	Vérifie que les méthodes définies par les tableaux se trouve dans la classe c. Un tableau de String (tab) est retourné, si la 
	 *			méthode i est trouvée, tab[i] == null, sinon tab[i] est un message d'erreur
	 */
	public static String [] inspect_methods(Class c,int [] modifier,Class [] return_type, String [] name,Class [][] expected_param, Class [][] expected_exception) {
		String [] tab = new String [modifier.length];
		for(int i = 0;i<tab.length;i++)
			tab[i] = check_method(c,(modifier != null) ? modifier[i] : -1,return_type[i],name[i],expected_param[i],(expected_exception != null) ? expected_exception[i] : null);
		return tab;
	}

	/**
	 * Cette méthode va chercher dans la classe c une méthode avec les contrainte suivante:
	 *		- L'entier représentant le modificateur de la méthode est modifier
	 *		- Le type de retour de la méthode est de type return_type
	 *		- Le nom de la méthode est name
	 *		- L'ensemble des type des paramètre de la fonction est une permutation de expected_param
	 *		- L'ensemble des erreurs qui sont "throws" par la méthode est une permutation de expected_exception
	 *
	 * @pre		c != null, name != null, expected param != null expected_exception != null,
	 *			chaque classe dans expected_exception apparait une seule fois dans le tableau,
	 *			modifier représente un modificateur comme définit dans la classe java.lang.reflect.modifier
	 *
	 * @post	Cherche une fonction sous les contraintes énoncée plus haut. Si elle est trouvée, renvoie null, 
	 *			sinon renvoie un message d'erreur
	 */
	private static String check_method(Class c, int modifier, Class return_type, String name, Class [] expected_param, Class [] expected_exception) {
		for(Method m : c.getDeclaredMethods()) {
			if(check_modifiers(m.getModifiers(),modifier)) {
				if(check_classes(m.getReturnType(),return_type)) {
					if(m.getName().equals(name)) {
						if(check_param(m.getParameterTypes(),expected_param)) {
							if(check_exception(m.getExceptionTypes(),expected_exception)) {
								return null;
							}
						}
					}
				}
			}
		}
		String error_msg;
		String feed;
		if(modifier != -1 && expected_exception != null){
			 error_msg = _("La méthode avec comme modificateur [{0}], comme type de retour {1}, comme nom {2}, comme type d''arguments {3} et comme exceptions déclarée via throws {4} n''as pas été trouvée !");
			 feed = MessageFormat.format(error_msg,Modifier.toString(modifier),return_type.toString(),name,Arrays.toString(expected_param),Arrays.toString(expected_exception));
		}
		else if(modifier != -1 && expected_exception == null) {
			error_msg = _("La méthode avec comme modificateur [{0}], comme type de retour {1}, comme nom {2}, comme type d''arguments {3} n''as pas été trouvée !");
			feed = MessageFormat.format(error_msg,Modifier.toString(modifier),return_type.toString(),name,Arrays.toString(expected_param));
		} else if (modifier == -1 && expected_exception != null) {
			 error_msg = _("La méthode avec comme type de retour {0}, comme nom {1}, comme type d''arguments {2} et comme exceptions déclarée via throws {3} n''as pas été trouvée !");
			 feed = MessageFormat.format(error_msg,return_type.toString(),name,Arrays.toString(expected_param),Arrays.toString(expected_exception));
		} else {
			 error_msg = _("La méthode avec comme type de retour {0}, comme nom {1}, comme type d''arguments {2} n''as pas été trouvée !");
			 feed = MessageFormat.format(error_msg,return_type.toString(),name,Arrays.toString(expected_param));
		} 
		return feed;
	}

	/**
	 * @pre		-
	 * @post	Vérifie si actual_modifier == expected_modifier.
	 * */
	private static boolean check_modifiers(int actual_modifier, int expected_modifier) {
		return (expected_modifier == -1) ? true : actual_modifier == expected_modifier;
	}

	/**
	 * @pre		classes != null
	 * @post	Retourne un tableau contenant les String représentant
	 *			les classes de classes
	 */
	public static String [] classes_toString(Class [] classes) {
		String [] t = new String[classes.length];
		for(int i=0;i<classes.length;i++)
			t[i] = classes[i].getName();
		return t;
	}

	/**
	 * @pre		-
	 * @post	Vérifie que actual_param est une permutation de expected_param.
	 */
	private static boolean check_param(Class [] actual_param, Class [] expected_param) {
		if(actual_param.length != expected_param.length)
			return false;
		String [] name_actual = classes_toString(actual_param);
		String [] name_expected = classes_toString(expected_param);
		Arrays.sort(name_actual);
		Arrays.sort(name_expected);
		return Arrays.equals(name_actual,name_expected);
	}

	/**
	 * @pre		-
	 * @post	Vérifie que actual_thrown_exception == expected_exception
	 */
	private static boolean check_exception(Class [] actual_thrown_exception, Class [] expected_exception){
		if(expected_exception == null)
			return true;
		if(actual_thrown_exception.length != expected_exception.length)
			return false;
		String [] name_actual = classes_toString(actual_thrown_exception);
		String [] name_expected = classes_toString(expected_exception);
		Arrays.sort(name_actual);
		Arrays.sort(name_expected);
		return Arrays.equals(name_actual,name_expected);
	}


	/**
	 * @pre		-
	 * @post	Vérifie que les deux classes sont les même
	 */
	private static boolean check_classes(Class c1, Class c2) {
		return c1.getName().equals(c2.getName());
	}

	/**
	 * Cette méthode permet de récupérer la valeur d'une variable d'instance
	 * dans l'objet instance de type c, sans passer par les méthode écrite par 
	 * l'étudiant, via le nom du champ. Cette méthode demande donc de connaître le
	 * nom du champs.
	 *
	 * Si le noms du champs n'est pas connu, utilisez la méthode getInstanceValueFromType
	 *
	 * @pre		c != null, field != null
	 * @post	Retourne la valeur associés à la variable d'instance
	 *			field dans c ou null si aucune variable n'est trouvée
	 */
	public static Object getInstanceValueFromName(Class c,String field, Object instance) {
		try {
			Field f = c.getDeclaredField(field);
			boolean initAccess = f.isAccessible();
			f.setAccessible(true);
			f.setAccessible(initAccess);
			return f.get(instance);
		} catch ( NoSuchFieldException e) {
			return null;
		} catch ( IllegalAccessException e) {
			return null;
		}
	}

	/**
	 * Récupère l'ensemble des valeurs des variables d'instances de type 
	 * tpye. Le nom de la variable d'instance n'as pas d'importance ici. 
	 * Pour récupérer une valeur d'une variable d'instance dont on connait le 
	 * nom, il faut utiliser la méthode getInstanceValueFromName
	 *
	 * @pre		c != null, type != null, instance != null
	 * @post	Retourne une liste contenant l'ensemble des valeurs
	 *			des variables d'instance de type type. Si une erreur
	 *			survient, retourne null
	 */
	public static List<Object> getInstanceValueFromType(Class c,Class type,Object instance) {
		try {
			Field [] allField = c.getDeclaredFields();
			List<Object> l = new ArrayList<>();
			for(int i=0;i<allField.length;i++) {
				Class<?> cl = allField[i].getType();
				if(cl.getName().equals(c.getName())){
					boolean initAccess = allField[i].isAccessible();
					allField[i].setAccessible(true);
					l.add(allField[i].get(instance));
					allField[i].setAccessible(initAccess);
				}
			}
			return l;
		} catch( IllegalAccessException e) {
			return null;
		} 
	}

	/**
	 * Récupère l'ensemble des valeurs des variables d'instance.
	 *
	 * @pre		c != null, instance != null
	 * @post	Retourne un tableau contentant l'ensemble des valeurs
	 *			des variables d'instance. Si une erreur survient, retourne null.
	 */
	public static Object[] getAllInstanceValue(Class c,Object instance) {
		try {
			Field [] allField = c.getDeclaredFields();
			Object [] allValue = new Object [allField.length];
			for(int i=0;i<allField.length;i++){
				allField[i].setAccessible(true);
				boolean initAccess = allField[i].isAccessible();
				allValue[i] = allField[i].get(instance);
				allField[i].setAccessible(initAccess);
			}
			return allValue;
		} catch (IllegalAccessException e) {
			return null;
		}
	}

	/**
	 * Récupère l'ensemble des valeurs des variables d'instance de la classe mère
	 *
	 * @pre		c != null, instance != null
	 * @post	Retourne un tableau contenant l'ensemble des valeurs
	 *			des variables d'instances de la classe mère, ou null 
	 *			en cas d'erreur
	 */
	public static Object [] getAllParentInstanceValue(Class c, Object instance) {
		return getAllInstanceValue(c.getSuperclass(),instance);
	}
}
