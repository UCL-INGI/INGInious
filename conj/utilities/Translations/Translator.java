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

package student.Translations;
import java.util.ResourceBundle;
import java.util.Locale;
import java.io.FileReader;
import java.io.BufferedReader;

public class Translator {
    
    // Localisation des fichiers .properties contenant les traduction
    private static String bundleLocation = "Translations/translations_java/MessagesBundle";
    
    private static ResourceBundle myResources;
    private static boolean ok = true;
    
    // Si une erreur suivient en essayant de récupérer la langue définie par le script run, on utilise le français.
    private static String lang_error = "fr";
    
    // Fichier crée par le script run qui permet à Translator.java de savoir quelle langue prendre.
    private static String lang_file = "./lang";
    
    /*
     * @pre -
     * @post Retourne la traduction du String {s} en fonction de la langue définie dans le fichier "./lang".
     *       Retourne la chaine non traduite si le fichier de traduction pour la langue définie n'existe pas ou si une erreur est survenue.
     */
    public static String _(String s) {
        
        // Try to load once the bundle. If no bundle found, we use the String id instead of the translation.
        if(ok == true){
            try {
                if (myResources == null) {
                    myResources = ResourceBundle.getBundle(bundleLocation, new Locale(get_lang()), ResourceBundle.Control.getNoFallbackControl(ResourceBundle.Control.FORMAT_PROPERTIES));
                }
            } catch (Exception e){
                // No bundle found
            } finally {
                ok = false;
            }
        }
        
        if (myResources != null){
            try {
                return myResources.getString(s);
            } catch (Exception e) { // Can happen if translation is invalid).
                return s;
            }
        } else
            return s;
    }
    
    /*
     * Read the code lang ("en_US" for example) in the file "./lang" that run script should have created.
     * Retourne {lang_error} si un problème survient.
     */
    private static String get_lang(){
        BufferedReader br = null;
        try {
            br = new BufferedReader(new FileReader(lang_file));
            return br.readLine().replace("\n\r", "").replace("\n", "").replace(" ", ""); //Delete evantual unwanted characters
        } catch(Exception e){
            return lang_error;
        } finally {
            try{
                br.close();
            }catch(Exception e){
                return lang_error;
            }
        }
    }
}
