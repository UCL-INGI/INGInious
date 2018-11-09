/**
 *  Copyright (c)  2017 Olivier Martin
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

import static org.junit.Assert.fail;
import java.text.MessageFormat;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;

import static student.Translations.Translator._;
import StudentCode.Etudiant;

public class FunctionHelper {
    
    /*
     *  Vérifie si :
     *      - une fonction {fun_name} existe dans la classe Etudiant
     *      - le type de retour de la fonction de l'étudiant est egal à {expected_type}
     *      - si les arguments sont du bon type
     */
    public static void check_etudiant_function(String class_name, String fun_name, Class expected_type, Class[] expected_parameters) throws ClassNotFoundException {
        check_etudiant_function_with_subquestion(class_name, fun_name, expected_type, expected_parameters, "");
    }
    
    public static void check_etudiant_function_with_subquestion(String class_name, String fun_name, Class expected_type, Class[] expected_parameters, String codeQuestion) throws ClassNotFoundException {
        
        Class<?> c = Class.forName(class_name);
        boolean methodFound = false;
        // On cherche la methode désirée parmis les méthodes de la classe Etudiant
        for (Method method : c.getDeclaredMethods()) {
            if(method.getName().equals(fun_name)){
                methodFound = true;
                if(! method.getReturnType().equals(expected_type)){
                    fail(MessageFormat.format(codeQuestion + _("Le type de retour de votre fonction doit être du type {0} !\n"), expected_type.toString()));
                }
                if(method.getGenericParameterTypes().length != expected_parameters.length){
                    fail(MessageFormat.format(codeQuestion + _("Votre fonction doit prendre {0} argument(s) !\n"), expected_parameters.length));
                }
                for(int i = 0; i < expected_parameters.length; i++){
                    if(! method.getGenericParameterTypes()[i].equals(expected_parameters[i])){
                        fail(MessageFormat.format(codeQuestion + _("L''argument n°{0} n''est pas de type ''{1}'' comme demandé !\n"), i+1, expected_parameters[i].toString()));
                    }
                }
            }
        }
        if(!methodFound)
            fail(codeQuestion + _("Votre fonction n'a pas été définie correctement. Assurez vous que son nom est correctement défini !\n") + MessageFormat.format(_("Le nom attendu est : ''{0}''.\n"), fun_name));
    }
    
    /*
     *  @pre Cette fonction suppose que la fonction {fun_name} avec les bon paramètres existe dans la classe Etudiant et est correcte.
     *      Exécutez la fonction check_etudiant_function() pour vous en assurer.
     *  @post Exécute la fonction {fun_name} et retourne le résultat sous forme d'Object.
     */
    public static Object run_student_function(String fun_name, Object... parameters) throws IllegalAccessException, IllegalArgumentException, InvocationTargetException {
        Etudiant etu = new Etudiant();
        Class c = new Etudiant().getClass();
        
        // On cherche la methode désirée parmis les méthodes de la classe Etudiant, suppose qu'il n'y a qu'une méthode portant le nom {fun_name}
        for (Method method : c.getDeclaredMethods()) {
            if(method.getName().equals(fun_name)){
                method.setAccessible(true); //important
                return method.invoke(etu, parameters);
            }
        }
        return null;
    }
}
